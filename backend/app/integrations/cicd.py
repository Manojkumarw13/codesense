"""CI/CD provider connector — Phase 21 Task 5.

Implements :class:`BaseProviderConnector` for generic CI/CD (GitHub Actions,
GitLab CI, Jenkins-style):

* Bearer token auth headers
* paginated REST event fetching (``/builds`` or ``/events``) with cursor
  pagination; webhook-only mode when ``base_url`` is not configured
* mapping CI/CD events to ProviderEventCreate-shaped raw events:
  - build started → ``BUILD_STARTED``
  - build succeeded → ``BUILD_COMPLETED`` + ``BUILD_SUCCEEDED``
  - build failed → ``BUILD_COMPLETED`` + ``BUILD_FAILED``
  - deployment created → ``DEPLOYMENT_CREATED``
  - deployment succeeded → ``DEPLOYMENT_SUCCEEDED``
  - deployment failed → ``DEPLOYMENT_FAILED``
* HMAC-SHA256 webhook signature verification
* webhook payload mapping

The connector registers itself with the module-level :data:`registry` at
import time so the API layer can look it up by name (``"cicd"``).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import requests

from backend.app.integrations.base import BaseProviderConnector
from backend.app.integrations.registry import registry

logger = logging.getLogger("codesense.integrations.cicd")


class CICDError(Exception):
    """Raised when the CI/CD API returns a non-2xx response."""


class CICDConnector(BaseProviderConnector):
    """Generic CI/CD REST API connector.

    Reads its token, webhook secret, and ``base_url`` from ``config``
    (set on the :class:`ConnectorConfig`). ``base_url`` is optional; when
    absent, ``fetch_events`` returns an empty page (webhook-only mode).
    """

    PER_PAGE = 100
    REQUEST_TIMEOUT_SECONDS = 30

    def __init__(
        self,
        connector_id: uuid.UUID,
        org_id: uuid.UUID,
        config: dict[str, Any],
    ) -> None:
        super().__init__(connector_id, org_id, config)
        self._session = requests.Session()

    # --- auth ---

    def auth_headers(self) -> dict[str, str]:
        """HTTP headers for authenticated CI/CD API calls.

        Omits Authorization header when no token is configured.
        """
        token = self.config.get("token", "")
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    # --- fetch ---

    def fetch_events(
        self,
        since: datetime | None = None,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """Fetch a single page of CI/CD events (builds/deployments).

        Returns ``(events, next_cursor, has_more)`` where ``next_cursor`` is
        the next cursor string (or ``None`` when there is no next page) and
        ``has_more`` reflects the presence of a next cursor.

        If ``base_url`` is not configured, returns ``([], None, False)``
        to indicate webhook-only mode.

        Passes ``since`` as an ISO8601 query parameter to the API for
        server-side filtering (falling back to client-side filtering via
        ``_filter_by_since``).
        """
        base_url = self.config.get("base_url", "")
        if not base_url:
            return [], None, False

        url = f"{base_url.rstrip('/')}/events"

        params: dict[str, Any] = {"limit": self.PER_PAGE}
        if cursor:
            params["cursor"] = cursor
        if since:
            params["since"] = self._format_since_for_query(since)

        resp = self._session.get(
            url,
            headers=self.auth_headers(),
            params=params,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        if resp.status_code >= 400:
            raise CICDError(
                f"CI/CD API returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise CICDError(
                f"CI/CD API returned non-JSON response (HTTP {resp.status_code})"
            ) from exc

        # Handle both array and object responses
        if isinstance(data, dict):
            page_events = data.get("items", data.get("events", data.get("builds", [])))
        elif isinstance(data, list):
            page_events = data
        else:
            page_events = []

        events = self._filter_by_since(page_events, since)  # type: ignore[arg-type]

        next_cursor = resp.headers.get("X-Next-Cursor")
        if next_cursor:
            return events, next_cursor, True
        return events, None, False

    # --- mapping ---

    def map_to_raw_events(
        self,
        team_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        repo_id: uuid.UUID | None = None,
        payloads: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Map CI/CD event dicts to ProviderEventCreate-shaped raw events."""
        return self._build_raw_events(payloads, source="poll")

    def webhook_to_raw_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Map an inbound CI/CD webhook payload to raw events.

        The caller is expected to ensure the payload contains ``"type"``
        (or ``"event_type"``) and ``"status"`` fields so the event type
        can be resolved by ``_resolve_event_types``.
        """
        merged = dict(payload)
        # Don't overwrite "type" if already present; "event" is just metadata
        return self._build_raw_events([merged], source="webhook")

    def _build_raw_events(
        self, payloads: list[dict[str, Any]] | None, source: str
    ) -> list[dict[str, Any]]:
        raw_events: list[dict[str, Any]] = []
        for payload in payloads or []:
            event_types = self._resolve_event_types(payload)
            if not event_types:
                continue
            event_id = payload.get("id")
            if event_id is None:
                continue
            for event_type in event_types:
                raw_events.append(
                    {
                        "provider": "cicd",
                        "external_event_id": f"cicd:{event_id}",
                        "event_type": event_type,
                        "event_timestamp": self._parse_timestamp(
                            payload.get("created_at")
                        ),
                        "payload": dict(payload),
                        "source": source,
                    }
                )
        return raw_events

    def _resolve_event_types(self, payload: dict[str, Any]) -> list[str]:
        """Resolve CI/CD event types from a payload.

        Returns a list of event types (can be multiple for build completed
        events which emit both BUILD_COMPLETED and BUILD_SUCCEEDED/FAILED).
        """
        event_type = str(payload.get("type") or payload.get("event_type") or "")
        status = str(payload.get("status") or "")

        if event_type == "build":
            if status == "started":
                return ["BUILD_STARTED"]
            if status in ("success", "succeeded"):
                return ["BUILD_COMPLETED", "BUILD_SUCCEEDED"]
            if status in ("failed", "failure", "error"):
                return ["BUILD_COMPLETED", "BUILD_FAILED"]
            return []

        if event_type == "deployment":
            if status == "created":
                return ["DEPLOYMENT_CREATED"]
            if status in ("success", "succeeded"):
                return ["DEPLOYMENT_SUCCEEDED"]
            if status in ("failed", "failure", "error"):
                return ["DEPLOYMENT_FAILED"]
            return []

        return []

    def verify_webhook_signature(
        self, payload: bytes, signature: str | None = None
    ) -> bool:
        """Verify an inbound CI/CD webhook HMAC-SHA256 signature.

        Expects signature in the format ``sha256=<hexdigest>``.
        """
        if not signature:
            return False
        secret = self.config.get("webhook_secret", "").encode("utf-8")
        expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    # --- helpers ---

    @staticmethod
    def _format_since_for_query(since: datetime | str | None) -> str | None:
        """Format ``since`` as an ISO8601 string for query parameters.

        ``BaseProviderConnector.fetch_events`` types ``since`` as
        ``datetime | None``, but the API expects an ISO-8601 string.
        A ``datetime`` is formatted with an explicit UTC offset; an
        already-string ``since`` is normalized (e.g., "Z" -> "+0000")
        so callers (and tests) can supply raw ISO8601 strings.
        """
        if since is None:
            return None
        if isinstance(since, datetime):
            return since.strftime("%Y-%m-%dT%H:%M:%S%z")
        text = str(since).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+0000"
        return text

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            logger.warning("Could not parse CI/CD timestamp %r", value)
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def _filter_by_since(
        self, events: list[dict[str, Any]], since: datetime | None
    ) -> list[dict[str, Any]]:
        since_dt = self._parse_timestamp(since) if since is not None else None
        if since_dt is None:
            return list(events)
        filtered: list[dict[str, Any]] = []
        for event in events:
            event_dt = self._parse_timestamp(event.get("created_at"))
            if event_dt is None:
                continue
            if event_dt >= since_dt:
                filtered.append(event)
        return filtered


# Register at import time so the API layer can look the connector up by name.
registry.register("cicd", CICDConnector)
