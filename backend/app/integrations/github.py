"""GitHub provider connector — Phase 21 Task 2.

Implements :class:`BaseProviderConnector` for GitHub:

* token-based auth headers
* paginated REST event fetching (``/repos/{owner}/{repo}/events``)
* mapping GitHub events to ProviderEventCreate-shaped raw events
* HMAC-SHA256 webhook signature verification
* webhook payload mapping

The connector registers itself with the module-level :data:`registry` at
import time so the API layer can look it up by name (``"github"``).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar

import requests

from backend.app.integrations.base import BaseProviderConnector
from backend.app.integrations.registry import registry

logger = logging.getLogger("codesense.integrations.github")


class GitHubError(Exception):
    """Raised when the GitHub API returns a non-2xx response."""


class GitHubConnector(BaseProviderConnector):
    """GitHub REST API connector.

    Reads its token and webhook secret from ``config`` (set on the
    :class:`ConnectorConfig`). ``owner``/``repo`` default to ``"o"``/``"r"``
    when not configured, keeping the connector usable out of the box.
    """

    BASE_URL = "https://api.github.com"

    DEFAULT_OWNER = "o"
    DEFAULT_REPO = "r"
    PER_PAGE = 100
    REQUEST_TIMEOUT_SECONDS = 30

    # GitHub event type -> event_type (action independent).
    _SIMPLE_TYPE_TO_TYPE: ClassVar[dict[str, str]] = {
        "PullRequestReviewEvent": "REVIEW_COMPLETED",
        "DeploymentEvent": "DEPLOYMENT_CREATED",
        "IssuesEvent": "WORK_ITEM_CREATED",
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
        """HTTP headers for authenticated GitHub API calls."""
        token = self.config.get("token", "")
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # --- fetch ---

    def fetch_events(
        self,
        since: datetime | None = None,
        cursor: str | None = None,
        owner: str | None = None,
        repo: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """Fetch a single page of repository events from GitHub.

        Returns ``(events, next_cursor, has_more)`` where ``next_cursor`` is
        the next page number as a string (or ``None`` when there is no next
        page) and ``has_more`` reflects the ``Link: rel="next"`` header.
        """
        owner = owner or self.config.get("owner", self.DEFAULT_OWNER)
        repo = repo or self.config.get("repo", self.DEFAULT_REPO)
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/events"

        page = int(cursor) if cursor and cursor.isdigit() else 1
        params: dict[str, Any] = {"per_page": self.PER_PAGE, "page": page}

        resp = self._session.get(
            url,
            headers=self.auth_headers(),
            params=params,
            timeout=self.REQUEST_TIMEOUT_SECONDS,
        )
        if resp.status_code >= 400:
            raise GitHubError(
                f"GitHub API returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        page_events = data if isinstance(data, list) else []
        events = self._filter_by_since(page_events, since)

        next_page = self._next_page_from_link(resp.headers.get("Link", ""))
        if next_page is not None:
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
        """Map GitHub event dicts to ProviderEventCreate-shaped raw events."""
        return self._build_raw_events(payloads, source="poll")

    def webhook_to_raw_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Map an inbound GitHub webhook payload to raw events.

        The caller is expected to merge the ``X-GitHub-Event`` header value
        into the payload under the ``"event"`` key (or ``"X-GitHub-Event"``)
        so the event type can be resolved.
        """
        merged = dict(payload)
        event_name = merged.get("event") or merged.get("X-GitHub-Event")
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
            raw_events.append(
                {
                    "provider": "github",
                    "external_event_id": f"github:{payload.get('id')}",
                    "event_type": event_type,
                    "event_timestamp": self._parse_timestamp(payload.get("created_at")),
                    "payload": dict(payload),
                    "source": source,
                }
            )
        return raw_events

    def _resolve_event_type(self, payload: dict[str, Any]) -> str | None:
        event_name = payload.get("type") or ""
        action = payload.get("action")

        if event_name in ("PullRequestEvent", "pull_request"):
            return (
                "CHANGE_CREATED"
                if action in ("opened", "reopened")
                else "CHANGE_UPDATED"
            )

        if event_name == "PullRequestReviewEvent":
            return self._SIMPLE_TYPE_TO_TYPE["PullRequestReviewEvent"]

        if event_name == "CheckRunEvent":
            if action == "started":
                return "BUILD_STARTED"
            if action == "completed":
                return "BUILD_COMPLETED"
            return None

        if event_name == "DeploymentEvent":
            return self._SIMPLE_TYPE_TO_TYPE["DeploymentEvent"]

        if event_name == "IssuesEvent":
            return self._SIMPLE_TYPE_TO_TYPE["IssuesEvent"]

        return None

    def verify_webhook_signature(
        self, payload: bytes, signature: str | None = None
    ) -> bool:
        """Verify an inbound GitHub webhook HMAC-SHA256 signature."""
        if not signature:
            return False
        secret = self.config.get("webhook_secret", "").encode("utf-8")
        expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

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
            logger.warning("Could not parse GitHub timestamp %r", value)
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

    @staticmethod
    def _next_page_from_link(link_header: str) -> int | None:
        """Parse the ``Link`` header and return the next page number, if any."""
        if not link_header:
            return None
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' not in part:
                continue
            match = re.search(r"<([^>]*)>", part)
            if not match:
                continue
            page_match = re.search(r"[?&]page=(\d+)", match.group(1))
            if page_match:
                return int(page_match.group(1))
        return None


# Register at import time so the API layer can look the connector up by name.
registry.register("github", GitHubConnector)
