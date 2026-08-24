import uuid
import pytest
from datetime import datetime, timedelta, timezone
from backend.app.services.detection import DetectionEngine
from backend.app.models.core import Team, Organization
from backend.app.models.analytics import MetricValue, MetricDefinition, Anomaly, Bottleneck
from backend.app.core.database import SessionLocal, engine

def test_anomaly_and_bottleneck_detection():
    db = SessionLocal()
    try:
        org_id = uuid.uuid4()
        team_id = uuid.uuid4()
        
        org = Organization(id=org_id, name="Test Org")
        team = Team(id=team_id, name="Test Team", organization_id=org_id)
        db.add_all([org, team])
        
        # Metric Definitions
        defs = {
            "review_backlog": MetricDefinition(id=uuid.uuid4(), metric_key="review_backlog", name="Review Backlog"),
            "review_turnaround": MetricDefinition(id=uuid.uuid4(), metric_key="review_turnaround", name="Review Turnaround"),
            "pipeline_duration": MetricDefinition(id=uuid.uuid4(), metric_key="pipeline_duration", name="Pipeline Duration"),
            "build_success_rate": MetricDefinition(id=uuid.uuid4(), metric_key="build_success_rate", name="Build Success Rate"),
        }
        for d in defs.values(): db.add(d)
        db.commit()
        
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        end = now
        
        # Current period metrics showing massive increase (e.g., > 10% change)
        mv_rb = MetricValue(
            id=uuid.uuid4(), metric_id=defs["review_backlog"].id, team_id=team_id, 
            period_start=start, period_end=end, value=50, change_percentage=25.0
        )
        mv_rt = MetricValue(
            id=uuid.uuid4(), metric_id=defs["review_turnaround"].id, team_id=team_id, 
            period_start=start, period_end=end, value=3600*24, change_percentage=30.0
        )
        # CI getting slower but still succeeding
        mv_pd = MetricValue(
            id=uuid.uuid4(), metric_id=defs["pipeline_duration"].id, team_id=team_id, 
            period_start=start, period_end=end, value=600, change_percentage=15.0
        )
        
        db.add_all([mv_rb, mv_rt, mv_pd])
        db.commit()
        
        engine_svc = DetectionEngine(db)
        
        # Detect bottlenecks
        bottlenecks = engine_svc.detect_bottlenecks(team_id, start, end)
        
        assert len(bottlenecks) >= 2
        categories = [b.category for b in bottlenecks]
        assert "REVIEW" in categories # backlog and turnaround both > 10%
        assert "CI" in categories # pipeline duration > 10%
        
        # Detect anomalies
        # Since we don't have history in this test, it will use fallback percentage > 50%
        # Let's add a metric with >50% change
        mv_bsr = MetricValue(
            id=uuid.uuid4(), metric_id=defs["build_success_rate"].id, team_id=team_id, 
            period_start=start, period_end=end, value=40, change_percentage=-60.0
        )
        db.add(mv_bsr)
        db.commit()
        
        anomalies = engine_svc.detect_anomalies(team_id, start, end)
        assert len(anomalies) == 1
        assert anomalies[0].metric_id == defs["build_success_rate"].id
        
    finally:
        db.rollback()
        db.close()
