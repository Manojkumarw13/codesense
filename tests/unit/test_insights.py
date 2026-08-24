import uuid
import pytest
from datetime import datetime, timedelta, timezone
from backend.app.services.insights import InsightsEngine
from backend.app.models.core import Team, Organization
from backend.app.models.analytics import Anomaly, Bottleneck, Insight, MetricDefinition
from backend.app.core.database import SessionLocal

def test_insights_generation_and_lifecycle():
    db = SessionLocal()
    try:
        org_id = uuid.uuid4()
        team_id = uuid.uuid4()
        
        org = Organization(id=org_id, name="Test Org")
        team = Team(id=team_id, name="Test Team", organization_id=org_id)
        db.add_all([org, team])
        db.commit()
        
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=1)
        end = now
        
        # Add bottleneck
        b = Bottleneck(
            id=uuid.uuid4(),
            organization_id=org_id,
            team_id=team_id,
            category="REVIEW",
            severity="HIGH",
            title="Review Bottleneck",
            description="Test desc",
            evidence={"review_turnaround": 50.0},
            detected_at=now - timedelta(hours=1)
        )
        db.add(b)
        
        # Add metric definition for anomaly
        md = MetricDefinition(id=uuid.uuid4(), metric_key="test_metric", name="Test Metric")
        db.add(md)
        db.commit()
        
        # Add anomaly
        a = Anomaly(
            id=uuid.uuid4(),
            organization_id=org_id,
            team_id=team_id,
            metric_id=md.id,
            severity="MEDIUM",
            baseline_value=10.0,
            observed_value=20.0,
            change_percent=100.0,
            evidence={},
            detected_at=now - timedelta(hours=1)
        )
        db.add(a)
        db.commit()
        
        # Generate insights
        engine = InsightsEngine(db)
        insights = engine.generate_insights_from_detections(team_id, start, end)
        
        assert len(insights) == 2
        assert insights[0].status == "ACTIVE"
        
        # Test lifecycle
        updated = engine.update_insight_status(insights[0].id, "REVIEWED")
        assert updated.status == "REVIEWED"
        
        updated = engine.update_insight_status(insights[0].id, "RESOLVED")
        assert updated.status == "RESOLVED"
        
    finally:
        db.rollback()
        db.close()
