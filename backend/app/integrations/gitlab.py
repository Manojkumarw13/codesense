"""GitLab provider connector — Phase 21 Task 3.

Implements :class:`BaseProviderConnector` for GitLab:

* ``Private-Token`` based auth headers
* paginated REST event fetching (``/projects/:id/events``)
* mapping GitLab events to ProviderEventCreate-shaped raw events
* webhook signature verification via ``X-Gitlab-Token``
* webhook payload mapping

The connector registers itself with the module-level :data:`registry` at
import time so the API layer can look it up by name (``"gitlab"``).
"""

from __future__ import annotations

import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar

import requests

from backend.app.integrations.base import BaseProviderConnector
from backend.app.integrations.registry import registry

logger = logging.getLogger("codesense.integrations.gitlab")


class GitLabError(Exception):
    """Raised when the GitLab API returns a non-2xx response."""


class GitLabConfigurationError(ValueError):
    """Raised when the GitLab connector is misconfigured (e.g. missing project_id)."""


class GitLabConnector(BaseProviderConnector):
    """GitLab REST API connector.

    Reads its token, webhook secret, and ``project_id`` from ``config``
    (set on the :class:`ConnectorConfig`). ``project_id`` is required;
    ``fetch_events`` raises :class:`GitLabConfigurationError` when it is
    absent.
    """

    BASE_URL = "https://gitlab.com/api/v4"

    PER_PAGE = 100
    REQUEST_TIMEOUT_SECONDS = 30

    # GitLab event target_type / action -> event_type (action independent).
    _SIMPLE_TYPE_TO_TYPE: ClassVar[dict[str, str]] = {
        "Deployment": "DEPLOYMENT_CREATED",
        "Issue": "WORK_ITEM_CREATED",
    }

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
        """HTTP headers for authenticated GitLab API calls."""
        token = self.config.get("token", "")
        return {
            "Private-Token": token,
        }

    # --- fetch ---

    def fetch_events(
        self,
        since: datetime | None = None,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """Fetch a single page of project events from GitLab.

        Returns ``(events, next_cursor, has_more)`` where ``next_cursor`` is
        the next page number as a string (or ``None`` when there is no next
        page) and ``has_more`` reflects the ``X-Next-Page`` header.
        """
        project_id = self.config.get("project_id")
        if not project_id:
            raise GitLabConfigurationError(
                "GitLabConnector requires 'project_id' in config"
            )
        url = f"{self.BASE_URL}/projects/{project_id}/events"

        page = int(cursor) if cursor and str(cursor).isdigit() else 1
        params: dict[str, Any] = {"per_page": self.PER_PAGE, "page": page}

        resp = self._session.get(
            url,
            headers=self.auth_headers(),
            params=params,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        if resp.status_code >= 400:
            raise GitLabError(
                f"GitLab API returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise GitLabError(
                f"GitLab API returned non-JSON response (HTTP {resp.status_code})"
            ) from exc
        page_events = data if isinstance(data, list) else []
        events = self._filter_by_since(page_events, since)

        next_page = resp.headers.get("X-Next-Page")
        if next_page and str(next_page).isdigit():
            return events, str(next_page), True
        return events, None, False

    # --- mapping ---

    def map_to_raw_events(
        self,
        team_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        repo_id: uuid.UUID | None = None,
        payloads: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Map GitLab event dicts to ProviderEventCreate-shaped raw events."""
        return self._build_raw_events(payloads, source="poll")

    def webhook_to_raw_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Map an inbound GitLab webhook payload to raw events.

        The caller is expected to merge the ``X-Gitlab-Event`` header value
        into the payload under the ``"event"`` key (or ``"X-Gitlab-Event"``)
        so the event type can be resolved.
        """
        merged = dict(payload)
        event_name = merged.get("event") or merged.get("X-Gitlab-Event")
        if event_name:
            merged["type"] = event_name
        return self._build_raw_events([merged], source="webhook")

    def _build_raw_events(
        self, payloads: list[dict[str, Any]] | None, source: str
    ) -> list[dict[str, Any]]:
        raw_events: list[dict[str, Any]] = []
        for payload in payloads or []:
            event_type = self._resolve_event_type(payload)
            if event_type is None:
                continue
            event_id = payload.get("id")
            if event_id is None:
                continue
            raw_events.append(
                {
                    "provider": "gitlab",
                    "external_event_id": f"gitlab:{event_id}",
                    "event_type": event_type,
                    "event_timestamp": self._parse_timestamp(payload.get("created_at")),
                    "payload": dict(payload),
                    "source": source,
                }
            )
        return raw_events

    def _resolve_event_type(self, payload: dict[str, Any]) -> str | None:
        event_name = str(payload.get("type") or payload.get("target_type") or "")
        action = str(payload.get("action_name") or payload.get("action") or "")
        status = str(payload.get("status") or "")

        if event_name in ("Merge Request", "MergeRequest"):
            if action == "approved":
                return "REVIEW_COMPLETED"
            if action in ("merged", "merge", "created", "opened"):
                return "CHANGE_CREATED"
            return "CHANGE_UPDATED"

        if event_name == "Pipeline":
            if status in ("success", "failed", "canceled", "stopped") or action in (
                "success",
                "failed",
                "canceled",
                "stopped",
            ):
                return "BUILD_COMPLETED"
            return "BUILD_STARTED"

        if event_name in self._SIMPLE_TYPE_TO_TYPE:
            return self._SIMPLE_TYPE_TO_TYPE[event_name]

        return None

    def verify_webhook_signature(
        self, payload: bytes, signature: str | None = None
    ) -> bool:
        """Verify an inbound GitLab webhook ``X-Gitlab-Token``.

        GitLab sends a plain secret token (not an HMAC) in the
        ``X-Gitlab-Token`` header; it is compared with the configured
        ``webhook_secret`` using a constant-time compare.
        """
        if not signature:
            return False
        secret = self.config.get("webhook_secret", "")
        return hmac.compare_digest(signature, secret)

    # --- helpers ---

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
            logger.warning("Could not parse GitLab timestamp %r", value)
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
registry.register("gitlab", GitLabConnector)
