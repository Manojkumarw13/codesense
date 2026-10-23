"""Provider connector base contract — Phase 21.

Every real provider connector (GitHub, GitLab, Jira, CI/CD) subclasses
BaseProviderConnector and implements the five abstract methods. Connectors
never write to the database directly: they produce ProviderEventCreate-shaped
dicts that are ingested through POST /api/v1/events/batch, and the existing
EventProcessor normalizes them into canonical events.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseProviderConnector(ABC):
    """Abstract contract for a provider connector."""

    def __init__(
        self,
        connector_id: uuid.UUID,
        org_id: uuid.UUID,
        config: dict[str, Any],
    ) -> None:
        self.connector_id = connector_id
        self.org_id = org_id
        self.config = dict(config or {})

    @abstractmethod
    def auth_headers(self) -> dict[str, str]:
        """HTTP headers for authenticated provider API calls."""

    @abstractmethod
    def fetch_events(
        self,
        since: datetime | None = None,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        """Fetch a page of provider events.

        Returns (events, next_cursor, has_more). `events` is a list of raw
        provider event dicts exactly as the provider API returns them.
        """

    @abstractmethod
    def map_to_raw_events(
        self,
        team_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        repo_id: uuid.UUID | None = None,
        payloads: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Map provider event dicts to ProviderEventCreate-shaped dicts."""

    @abstractmethod
    def verify_webhook_signature(
        self, payload: bytes, signature: str | None = None
    ) -> bool:
        """Verify an inbound webhook signature."""

    @abstractmethod
    def webhook_to_raw_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Map an inbound webhook payload to ProviderEventCreate-shaped dicts."""

    # --- sync state (concrete, stored in ConnectorConfig.config JSONB) ---

    def sync_state(self) -> dict[str, Any]:
        """Read the connector's sync state from its config blob."""
        return {
            "cursor": self.config.get("cursor"),
            "last_synced_at": self.config.get("last_synced_at"),
            "status": self.config.get("status", "never_synced"),
            "error": self.config.get("error"),
        }

    def update_sync_state(
        self,
        *,
        cursor: str | None = None,
        status: str | None = None,
        error: str | None = None,
        last_synced_at: str | None = None,
    ) -> dict[str, Any]:
        """Merge updates into the config blob (caller persists ConnectorConfig)."""
        if cursor is not None:
            self.config["cursor"] = cursor
        if status is not None:
            self.config["status"] = status
        if error is not None:
            self.config["error"] = error
        if last_synced_at is not None:
            self.config["last_synced_at"] = last_synced_at
        return self.sync_state()
