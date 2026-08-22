import uuid
from datetime import datetime, timezone
import pytest
from backend.app.core.database import SessionLocal
from backend.app.models.raw import ProviderEvent
from backend.app.models.core import (
    Organization,
    Team,
    Project,
    Repository,
    WorkItem,
    CanonicalEvent
)
from backend.app.services.processing import EventProcessor

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    try:
        # Delete children first
        db.query(CanonicalEvent).delete()
        db.query(WorkItem).delete()
        db.query(Repository).delete()
        db.query(Project).delete()
        db.query(Team).delete()
        db.query(Organization).delete()
        db.query(ProviderEvent).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(CanonicalEvent).delete()
        db.query(WorkItem).delete()
        db.query(Repository).delete()
        db.query(Project).delete()
        db.query(Team).delete()
        db.query(Organization).delete()
        db.query(ProviderEvent).delete()
        db.commit()
    finally:
        db.close()


def test_simulator_normalization_pipeline():
    """Verify that raw simulator events are correctly normalized into core relational models."""
    db = SessionLocal()
    try:
        # 1. Create raw provider event
        wi_id = f"wi-test-{uuid.uuid4().hex[:8]}"
        raw_event = ProviderEvent(
            provider="simulator",
            external_event_id=f"evt-{uuid.uuid4().hex[:8]}",
            event_type="WORK_ITEM_CREATED",
            payload={
                "organization_external_id": "sim-org-1",
                "organization_name": "Test Org",
                "team_external_id": "sim-team-1",
                "team_name": "Test Team",
                "project_external_id": "sim-proj-1",
                "project_name": "Test Project",
                "repository_external_id": "sim-repo-1",
                "repository_name": "Test Repo",
                "work_item_id": wi_id,
                "item_type": "FEATURE",
                "title": "Build Normalizer",
                "status": "BACKLOG",
                "priority": "HIGH",
                "actor_ref": "normalizer-test@codesense.io"
            },
            source="simulator"
        )
        db.add(raw_event)
        db.commit()
        
        # 2. Process the event
        processor = EventProcessor(db)
        count = processor.process_pending_events()
        assert count == 1
        
        # 3. Reload raw event and assert PROCESSED
        db.refresh(raw_event)
        assert raw_event.processing_status == "PROCESSED"
        assert raw_event.processed_at is not None
        
        # 4. Assert core entities were created and mapped
        org = db.query(Organization).filter_by(external_id="sim-org-1").first()
        assert org is not None
        assert org.name == "Test Org"
        
        team = db.query(Team).filter_by(external_id="sim-team-1").first()
        assert team is not None
        assert team.organization_id == org.id
        
        proj = db.query(Project).filter_by(external_id="sim-proj-1").first()
        assert proj is not None
        assert proj.team_id == team.id
        
        repo = db.query(Repository).filter_by(external_id="sim-repo-1").first()
        assert repo is not None
        assert repo.team_id == team.id
        
        wi = db.query(WorkItem).filter_by(external_id=wi_id).first()
        assert wi is not None
        assert wi.item_type == "FEATURE"
        assert wi.status == "BACKLOG"
        
        canonical_evt = db.query(CanonicalEvent).filter_by(raw_event_id=raw_event.id).first()
        assert canonical_evt is not None
        assert canonical_evt.event_type == "WORK_ITEM_CREATED"
        assert canonical_evt.actor_ref == "normalizer-test@codesense.io"
        assert canonical_evt.entity_type == "work_item"
        assert canonical_evt.entity_id == str(wi.id)
        
    finally:
        db.close()
