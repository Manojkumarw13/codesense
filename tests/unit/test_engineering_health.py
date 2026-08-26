import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.database import SessionLocal
from backend.app.models.analytics import MetricDefinition, MetricValue
from backend.app.models.core import Organization, Team
from backend.app.services.health import HealthScoreEngine


def test_engineering_health_score():
    db = SessionLocal()
    try:
        org_id = uuid.uuid4()
        team_id = uuid.uuid4()
        
        org = Organization(id=org_id, name="Test Org")
        db.add(org)
        
        team = Team(id=team_id, name="Test Team", organization_id=org_id)
        db.add(team)
        db.commit()
        
        # Add metric definitions
        defs = []
        for key in ["deployment_frequency", "build_success_rate"]:
            dfn = db.query(MetricDefinition).filter_by(metric_key=key).first()
            if not dfn:
                dfn = MetricDefinition(
                    id=uuid.uuid4(),
                    metric_key=key,
                    name=key.replace("_", " "),
                )
                db.add(dfn)
                db.commit()
            defs.append(dfn)
        
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        end = now
        
        # Add metric values
        mv1 = MetricValue(
            id=uuid.uuid4(),
            metric_id=defs[0].id,
            organization_id=org_id,
            team_id=team_id,
            period_start=start,
            period_end=end,
            value=10.0 # deployment_freq
        )
        mv2 = MetricValue(
            id=uuid.uuid4(),
            metric_id=defs[1].id,
            organization_id=org_id,
            team_id=team_id,
            period_start=start,
            period_end=end,
            value=95.0 # build_success_rate
        )
        db.add_all([mv1, mv2])
        db.commit()
        
        engine_svc = HealthScoreEngine(db)
        hs = engine_svc.calculate_health_score(team_id, start, end)
        
        assert hs is not None
        assert hs.score > 0
        assert "Delivery Flow" in hs.component_metrics
        assert "CI/CD Reliability" in hs.component_metrics
        
        # Delivery flow has weight 0.20 and we scored 10.0 freq which normalizes to 100.
        # So delivery flow score = 100
        assert hs.component_metrics["Delivery Flow"]["score"] == 100.0
        assert hs.component_metrics["CI/CD Reliability"]["score"] == 95.0
        
    finally:
        db.rollback()
        db.close()
