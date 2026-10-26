import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.database import SessionLocal
from backend.app.models.analytics import MetricDefinition, MetricValue
from backend.app.models.core import Organization, Team
from backend.app.services.health import HealthScoreEngine


def _setup_org_team(db):
    org_id = uuid.uuid4()
    team_id = uuid.uuid4()
    org = Organization(id=org_id, name="Health Org")
    team = Team(id=team_id, name="Health Team", organization_id=org_id)
    db.add_all([org, team])
    db.commit()
    return org_id, team_id


def _ensure_defs(db):
    keys = [
        "deployment_frequency",
        "lead_time",
        "cycle_time",
        "pr_cycle_time",
        "work_in_progress",
        "review_turnaround",
        "review_backlog",
        "build_success_rate",
        "pipeline_duration",
        "deployment_failure_rate",
        "change_failure_rate",
        "mttr",
    ]
    for key in keys:
        d = db.query(MetricDefinition).filter_by(metric_key=key).first()
        if not d:
            d = MetricDefinition(id=uuid.uuid4(), metric_key=key, name=key)
            db.add(d)
    db.commit()


def _add_metric(db, team_id, org_id, key, value, start, end):
    d = db.query(MetricDefinition).filter_by(metric_key=key).first()
    db.add(
        MetricValue(
            id=uuid.uuid4(),
            metric_id=d.id,
            organization_id=org_id,
            team_id=team_id,
            period_start=start,
            period_end=end,
            value=value,
        )
    )


def _period(days_back=7):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    return start, end


def test_perfect_health_score_is_one_hundred():
    db = SessionLocal()
    try:
        org_id, team_id = _setup_org_team(db)
        _ensure_defs(db)
        start, end = _period()
        # All metrics at "perfect" values -> every dimension normalizes to 100.
        _add_metric(db, team_id, org_id, "deployment_frequency", 10.0, start, end)
        _add_metric(db, team_id, org_id, "lead_time", 0.0, start, end)
        _add_metric(db, team_id, org_id, "cycle_time", 0.0, start, end)
        _add_metric(db, team_id, org_id, "pr_cycle_time", 0.0, start, end)
        _add_metric(db, team_id, org_id, "work_in_progress", 0.0, start, end)
        _add_metric(db, team_id, org_id, "review_turnaround", 0.0, start, end)
        _add_metric(db, team_id, org_id, "review_backlog", 0.0, start, end)
        _add_metric(db, team_id, org_id, "build_success_rate", 100.0, start, end)
        _add_metric(db, team_id, org_id, "pipeline_duration", 0.0, start, end)
        _add_metric(db, team_id, org_id, "deployment_failure_rate", 0.0, start, end)
        _add_metric(db, team_id, org_id, "change_failure_rate", 0.0, start, end)
        _add_metric(db, team_id, org_id, "mttr", 0.0, start, end)
        db.commit()

        engine = HealthScoreEngine(db)
        hs = engine.calculate_health_score(team_id, start, end)
        assert hs.score == 100.0
        assert set(hs.component_metrics.keys()) == {
            "Delivery Flow",
            "Development Flow",
            "Review Flow",
            "CI/CD Reliability",
            "Deployment Health",
            "Operational Health",
        }
        for data in hs.component_metrics.values():
            assert data["score"] == 100.0
    finally:
        db.rollback()
        db.close()


def test_partial_metrics_scale_to_hundred():
    db = SessionLocal()
    try:
        org_id, team_id = _setup_org_team(db)
        _ensure_defs(db)
        start, end = _period()
        # Only Delivery Flow metrics present: deployment_frequency = 10 -> norm 100.
        _add_metric(db, team_id, org_id, "deployment_frequency", 10.0, start, end)
        db.commit()

        engine = HealthScoreEngine(db)
        hs = engine.calculate_health_score(team_id, start, end)
        # total_weight = 0.20 < 1.0, so score is scaled up to 100.
        assert hs.score == 100.0
        assert hs.component_metrics["Delivery Flow"]["weight"] == 0.20
    finally:
        db.rollback()
        db.close()


def test_previous_score_and_change_are_recorded():
    db = SessionLocal()
    try:
        org_id, team_id = _setup_org_team(db)
        _ensure_defs(db)
        now = datetime.now(timezone.utc)
        prev_start = now - timedelta(days=14)
        prev_end = now - timedelta(days=7)
        cur_start = now - timedelta(days=7)
        cur_end = now

        # Previous period: perfect score
        _add_metric(
            db, team_id, org_id, "deployment_frequency", 10.0, prev_start, prev_end
        )
        db.commit()
        engine = HealthScoreEngine(db)
        prev_hs = engine.calculate_health_score(team_id, prev_start, prev_end)
        assert prev_hs.score == 100.0

        # Current period: zero deployment frequency -> Delivery Flow norm 0 -> score 0
        _add_metric(
            db, team_id, org_id, "deployment_frequency", 0.0, cur_start, cur_end
        )
        db.commit()
        cur_hs = engine.calculate_health_score(team_id, cur_start, cur_end)
        assert cur_hs.previous_score == 100.0
        assert cur_hs.score_change == -100.0
    finally:
        db.rollback()
        db.close()


def test_health_score_has_components_with_weights():
    db = SessionLocal()
    try:
        org_id, team_id = _setup_org_team(db)
        _ensure_defs(db)
        start, end = _period()
        _add_metric(db, team_id, org_id, "deployment_frequency", 10.0, start, end)
        _add_metric(db, team_id, org_id, "build_success_rate", 100.0, start, end)
        db.commit()

        engine = HealthScoreEngine(db)
        hs = engine.calculate_health_score(team_id, start, end)
        # Delivery Flow and CI/CD Reliability present; others skipped (no metrics).
        assert "Delivery Flow" in hs.component_metrics
        assert "CI/CD Reliability" in hs.component_metrics
        assert hs.component_metrics["Delivery Flow"]["weight"] == 0.20
        assert hs.component_metrics["CI/CD Reliability"]["weight"] == 0.15
    finally:
        db.rollback()
        db.close()
