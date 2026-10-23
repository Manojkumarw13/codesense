"""Jira provider connector — Phase 21 Task 4.

Implements :class:`BaseProviderConnector` for Jira (Cloud/Server):

* Basic auth (``email`` + ``api_token``) or Bearer token (``pat``) auth headers
* paginated REST issue fetching (``/rest/api/3/search`` with JQL ``updated >= ...``)
  using ``maxResults``/``startAt`` pagination and the response's ``isLast`` flag
* mapping Jira issues to ProviderEventCreate-shaped raw events
* webhook secret header verification (``X-Webhook-Secret``)
* webhook payload mapping

The connector registers itself with the module-level :data:`registry` at
import time so the API layer can look it up by name (``"jira"``).
"""

from __future__ import annotations

import base64
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar

import requests

from backend.app.integrations.base import BaseProviderConnector
from backend.app.integrations.registry import registry

logger = logging.getLogger("codesense.integrations.jira")


class JiraError(Exception):
    """Raised when the Jira API returns a non-2xx response."""


class JiraConfigurationError(ValueError):
    """Raised when the Jira connector is misconfigured (e.g. missing base_url)."""


class JiraConnector(BaseProviderConnector):
    """Jira REST API connector.

    Reads ``base_url``, ``email``, ``api_token`` (or ``pat``), and
    ``webhook_secret`` from ``config`` (set on the :class:`ConnectorConfig`).
    ``base_url`` is required; ``fetch_events`` raises
    :class:`JiraConfigurationError` when it is absent.
    """

    MAX_RESULTS = 50
    REQUEST_TIMEOUT_SECONDS = 30

    # Jira status names that map to review-related event types.
    _REVIEW_STATUSES: ClassVar[frozenset[str]] = frozenset({"In Review", "Code Review"})
    _DONE_STATUSES: ClassVar[frozenset[str]] = frozenset({"Done", "Resolved"})

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
        """HTTP headers for authenticated Jira API calls.

        Uses Bearer ``pat`` when configured, otherwise Basic auth with
        ``email`` + ``api_token``.
        """
        pat = self.config.get("pat", "")
        if pat:
            return {
                "Authorization": f"Bearer {pat}",
                "Accept": "application/json",
            }
        email = self.config.get("email", "")
        api_token = self.config.get("api_token", "")
        credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode("ascii")
        return {
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json",
        }

    # --- fetch ---

    def fetch_events(
        self,
        since: datetime | None = None,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """Fetch a single page of Jira issues updated since ``since``.

        Calls ``/rest/api/3/search`` with JQL ``updated >= ...`` and
        ``maxResults``/``startAt`` pagination. Returns
        ``(events, next_cursor, has_more)`` where ``next_cursor`` is the next
        ``startAt`` value (as a string) when there are more results and
        ``has_more`` is the inverse of the response's ``isLast`` flag.
        """
        base_url = self.config.get("base_url", "")
        if not base_url:
            raise JiraConfigurationError("JiraConnector requires 'base_url' in config")

        url = f"{base_url.rstrip('/')}/rest/api/3/search"

        start_at = int(cursor) if cursor and str(cursor).isdigit() else 0
        since_jql = self._format_since_for_jql(since)
        jql = f'updated >= "{since_jql}"' if since_jql else "updated >= -1w"
        params: dict[str, Any] = {
            "jql": jql,
            "maxResults": self.MAX_RESULTS,
            "startAt": start_at,
        }

        resp = self._session.get(
            url,
            headers=self.auth_headers(),
            params=params,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        if resp.status_code >= 400:
            raise JiraError(
                f"Jira API returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise JiraError(
                f"Jira API returned non-JSON response (HTTP {resp.status_code})"
            ) from exc
        if not isinstance(data, dict):
            data = {}
        page_events = data.get("issues", [])
        if not isinstance(page_events, list):
            page_events = []
        events = self._filter_by_since(page_events, since)

        is_last = data.get("isLast", True)
        if not is_last:
            next_cursor = str(start_at + len(page_events))
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
        """Map Jira issue dicts to ProviderEventCreate-shaped raw events."""
        return self._build_raw_events(payloads, source="poll")

    def webhook_to_raw_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Map an inbound Jira webhook payload to raw events.

        The caller is expected to merge the ``X-Webhook-Secret``/event type
        into the payload under the ``"webhookEvent"`` key (or ``"event"`` /
        ``"X-Webhook-Event"``) so the event type can be resolved.
        """
        merged = dict(payload)
        event_name = (
            merged.get("webhookEvent")
            or merged.get("event")
            or merged.get("X-Webhook-Event")
        )
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
            key = payload.get("key") or (payload.get("issue") or {}).get("key")
            if key is None:
                continue
            raw_events.append(
                {
                    "provider": "jira",
                    "external_event_id": f"jira:{key}",
                    "event_type": event_type,
                    "event_timestamp": self._parse_timestamp(
                        (payload.get("fields") or {}).get("updated")
                        or (payload.get("issue") or {}).get("fields", {}).get("updated")
                        or payload.get("created_at")
                    ),
                    "payload": dict(payload),
                    "source": source,
                }
            )
        return raw_events

    def _resolve_event_type(self, payload: dict[str, Any]) -> str | None:
        event_name = str(payload.get("webhookEvent") or payload.get("type") or "")
        fields = payload.get("fields") or {}
        if not fields and payload.get("issue"):
            fields = (payload.get("issue") or {}).get("fields") or {}

        # An explicitly created issue is always a work item.
        if event_name == "jira:issue_created":
            return "WORK_ITEM_CREATED"

        # Status-based resolution covers issue transitions (updated) and search
        # results, where the issue's current status drives the event type.
        if fields.get("deployment"):
            return "DEPLOYMENT_CREATED"

        status = fields.get("status") or {}
        status_name = str(status.get("name") or "")
        if status_name in self._DONE_STATUSES:
            return "REVIEW_COMPLETED"
        if status_name in self._REVIEW_STATUSES:
            return "REVIEW_REQUESTED"

        return "WORK_ITEM_CREATED"

    def verify_webhook_signature(
        self, payload: bytes, signature: str | None = None
    ) -> bool:
        """Verify an inbound Jira webhook ``X-Webhook-Secret`` header.

        Jira sends the configured webhook secret in the ``X-Webhook-Secret``
        header; it is compared with the configured ``webhook_secret`` using a
        constant-time compare.
        """
        if not signature:
            return False
        secret = self.config.get("webhook_secret", "")
        return hmac.compare_digest(signature, secret)

    # --- helpers ---

    @staticmethod
    def _format_since_for_jql(since: datetime | str | None) -> str | None:
        """Format ``since`` as a Jira JQL-compatible datetime literal.

        ``BaseProviderConnector.fetch_events`` types ``since`` as
        ``datetime | None``, but Jira JQL expects an ISO-8601 string such as
        ``"2026-01-01T00:00:00+0000"``. A ``datetime`` is formatted with an
        explicit UTC offset; an already-string ``since`` is passed through so
        callers (and tests) can keep supplying raw JQL literals.
        """
        if since is None:
            return None
        if isinstance(since, datetime):
            return since.strftime("%Y-%m-%dT%H:%M:%S%z")
        return str(since)

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
            logger.warning("Could not parse Jira timestamp %r", value)
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
            event_dt = self._parse_timestamp((event.get("fields") or {}).get("updated"))
            if event_dt is None:
                continue
            if event_dt >= since_dt:
                filtered.append(event)
        return filtered


# Register at import time so the API layer can look the connector up by name.
registry.register("jira", JiraConnector)
