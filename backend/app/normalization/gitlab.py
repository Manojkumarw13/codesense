import logging
from backend.app.models.raw import ProviderEvent
from backend.app.normalization.base import BaseNormalizer

logger = logging.getLogger("codesense.normalization.gitlab")

class GitLabNormalizer(BaseNormalizer):
    """Normalize GitLab webhook events (Placeholder for integration phase)."""
    def normalize(self, raw_event: ProviderEvent) -> None:
        logger.info(f"GitLab normalizer called for event type: {raw_event.event_type}")
        # Will be expanded during Phase 15.
        pass
