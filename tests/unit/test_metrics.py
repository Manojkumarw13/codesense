import uuid
import pytest
from datetime import datetime, timedelta, timezone
from backend.app.services.metrics import MetricEngine
from backend.app.models.core import Team, Deployment, Organization
from backend.app.models.analytics import MetricValue
from backend.app.core.database import SessionLocal, engine
from backend.app.models.base import Base

def test_deployment_frequency():
    db = SessionLocal()
    try:
        org_id = uuid.uuid4()
        team_id = uuid.uuid4()
        
        org = Organization(id=org_id, name="Test Org")
        db.add(org)
        db.commit()
        
        team = Team(id=team_id, name="Test Team", organization_id=org_id)
        db.add(team)
        db.commit()
        
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        end = now
        
        for i in range(3):
            dep = Deployment(
                id=uuid.uuid4(),
                team_id=team_id,
                provider="github",
                external_id=f"dep_{i}_{uuid.uuid4()}",
                status="SUCCESS",
                completed_at=start + timedelta(days=i)
            )
            db.add(dep)
        
        db.add(Deployment(
            id=uuid.uuid4(),
            team_id=team_id,
            provider="github",
            external_id=f"dep_fail_{uuid.uuid4()}",
            status="FAILURE",
            completed_at=start + timedelta(days=4)
        ))
        db.commit()
        
        engine_svc = MetricEngine(db)
        values = engine_svc.calculate_metrics_for_period(team_id, start, end)
        
        df_val = next(v for v in values if engine_svc.metric_defs["deployment_frequency"].id == v.metric_id)
        assert df_val.value == 3.0
        
        dfr_val = next(v for v in values if engine_svc.metric_defs["deployment_failure_rate"].id == v.metric_id)
        assert dfr_val.value == 25.0
        
    finally:
        db.rollback()
        db.close()
