import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.raw import ProviderEvent
from backend.app.normalization.simulator import SimulatorNormalizer
from backend.app.normalization.github import GitHubNormalizer
from backend.app.normalization.gitlab import GitLabNormalizer
from backend.app.normalization.jira import JiraNormalizer
from backend.app.core.exceptions import DatabaseError

logger = logging.getLogger("codesense.processing")

class EventProcessor:
    """Service responsible for background processing and normalisation of raw events."""
    
    def __init__(self, db: Session) -> None:
        self.db = db
        # Register normalizers
        self.normalizers = {
            "simulator": SimulatorNormalizer(db),
            "github": GitHubNormalizer(db),
            "gitlab": GitLabNormalizer(db),
            "jira": JiraNormalizer(db),
        }

    def process_pending_events(self, limit: int = 100) -> int:
        """Fetch up to limit PENDING raw events, normalize them, and update status."""
        events = (
            self.db.query(ProviderEvent)
            .filter(ProviderEvent.processing_status == "PENDING")
            .order_by(ProviderEvent.created_at.asc())
            .limit(limit)
            .all()
        )
        
        if not events:
            return 0
            
        processed_count = 0
        
        for event in events:
            # Set status to PROCESSING
            event.processing_status = "PROCESSING"
            self.db.commit()
            
            provider = event.provider.lower()
            normalizer = self.normalizers.get(provider)
            
            if not normalizer:
                logger.error(f"No normalizer registered for provider: {provider}")
                event.processing_status = "FAILED"
                self.db.commit()
                continue
                
            try:
                # Process the normalization
                normalizer.normalize(event)
                
                # Update raw event status to PROCESSED
                event.processing_status = "PROCESSED"
                event.processed_at = datetime.now(timezone.utc)
                self.db.commit()
                processed_count += 1
                
            except Exception as e:
                self.db.rollback()
                logger.exception(f"Failed to normalize raw event {event.id} from {provider}: {str(e)}")
                
                # Mark as FAILED
                event.processing_status = "FAILED"
                self.db.commit()
                
        return processed_count
