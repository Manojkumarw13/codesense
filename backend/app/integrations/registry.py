"""Provider connector registry — Phase 21.

Maps provider names (e.g. "github", "gitlab", "jira", "cicd") to their
connector classes. The API layer uses this to instantiate the right
connector for a ConnectorConfig.
"""

from __future__ import annotations

from backend.app.integrations.base import BaseProviderConnector


class ProviderRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, type[BaseProviderConnector]] = {}

    def register(self, name: str, connector_class: type[BaseProviderConnector]) -> None:
        self._connectors[name.lower()] = connector_class

    def get(self, name: str) -> type[BaseProviderConnector] | None:
        return self._connectors.get(name.lower())

    def list(self) -> list[str]:
        return sorted(self._connectors)


registry = ProviderRegistry()
