import logging
from typing import Any, cast

from backend.app.models.raw import ProviderEvent
from backend.app.normalization.base import BaseNormalizer

logger = logging.getLogger("codesense.normalization.github")


class GitHubNormalizer(BaseNormalizer):
    """Normalize GitHub provider events into canonical events."""

    def normalize(self, raw_event: ProviderEvent) -> None:
        org = self.get_or_create_organization("github", "GitHub")
        self.create_canonical_event(
            raw_event=raw_event,
            org_id=org.id,
            team_id=None,
            project_id=None,
            repo_id=None,
            event_type=cast(str, raw_event.event_type),
            occurred_at=raw_event.event_timestamp or raw_event.received_at,
            metadata=cast(dict[str, Any], raw_event.payload),
        )
