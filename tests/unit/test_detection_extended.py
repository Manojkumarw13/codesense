import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.database import SessionLocal
from backend.app.models.analytics import MetricDefinition, MetricValue
from backend.app.models.core import Organization, Team
from backend.app.services.detection import DetectionEngine


def _setup_org_team(db):
    org_id = uuid.uuid4()
    team_id = uuid.uuid4()
    org = Organization(id=org_id, name="Detect Org")
    team = Team(id=team_id, name="Detect Team", organization_id=org_id)
    db.add_all([org, team])
    db.commit()
    return org_id, team_id


def _ensure_defs(db, keys):
    for key in keys:
        d = db.query(MetricDefinition).filter_by(metric_key=key).first()
        if not d:
            d = MetricDefinition(id=uuid.uuid4(), metric_key=key, name=key)
            db.add(d)
    db.commit()


def _add_value(db, team_id, key, value, start, end, change_pct=None, baseline=None):
    d = db.query(MetricDefinition).filter_by(metric_key=key).first()
    db.add(
        MetricValue(
            id=uuid.uuid4(),
            metric_id=d.id,
            team_id=team_id,
            period_start=start,
            period_end=end,
            value=value,
            change_percentage=change_pct,
            baseline_value=baseline,
        )
    )


def _period(days_back=7):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    return start, end


def test_detect_anomalies_z_score_high_value():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["build_success_rate"])
        start, end = _period()
        # History: 5 values clustered around 90 -> mean ~90, low std dev.
        for v in [90, 88, 92, 89, 91]:
            _add_value(
                db,
                team_id,
                "build_success_rate",
                v,
                start - timedelta(days=7),
                start,
                change_pct=0.0,
            )
        # Current value far above history -> high z-score -> CRITICAL anomaly.
        _add_value(
            db,
            team_id,
            "build_success_rate",
            25.0,
            start,
            end,
            change_pct=-70.0,
            baseline=90.0,
        )
        db.commit()

        engine = DetectionEngine(db)
        anomalies = engine.detect_anomalies(team_id, start, end)
        assert len(anomalies) == 1
        assert anomalies[0].severity == "CRITICAL"
        assert anomalies[0].observed_value == 25.0
    finally:
        db.rollback()
        db.close()


def test_detect_anomalies_fallback_percent_change():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["deployment_frequency"])
        start, end = _period()
        # Only 1 history value (< 3) -> fallback to percentage change.
        _add_value(
            db,
            team_id,
            "deployment_frequency",
            5.0,
            start - timedelta(days=7),
            start,
            change_pct=0.0,
        )
        _add_value(
            db,
            team_id,
            "deployment_frequency",
            12.0,
            start,
            end,
            change_pct=140.0,
            baseline=5.0,
        )
        db.commit()

        engine = DetectionEngine(db)
        anomalies = engine.detect_anomalies(team_id, start, end)
        assert len(anomalies) == 1
        assert (
            anomalies[0].severity == "MEDIUM"
        )  # 140% > 100% -> MEDIUM? actually >100 is MEDIUM per code
    finally:
        db.rollback()
        db.close()


def test_detect_anomalies_small_change_no_anomaly():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["deployment_frequency"])
        start, end = _period()
        _add_value(
            db,
            team_id,
            "deployment_frequency",
            5.0,
            start - timedelta(days=7),
            start,
            change_pct=0.0,
        )
        _add_value(
            db,
            team_id,
            "deployment_frequency",
            6.0,
            start,
            end,
            change_pct=20.0,
            baseline=5.0,
        )
        db.commit()

        engine = DetectionEngine(db)
        anomalies = engine.detect_anomalies(team_id, start, end)
        assert anomalies == []
    finally:
        db.rollback()
        db.close()


def test_detect_bottlenecks_review_category():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["review_backlog", "review_turnaround"])
        start, end = _period()
        _add_value(db, team_id, "review_backlog", 30.0, start, end, change_pct=20.0)
        _add_value(
            db, team_id, "review_turnaround", 7200.0, start, end, change_pct=15.0
        )
        db.commit()

        engine = DetectionEngine(db)
        bottlenecks = engine.detect_bottlenecks(team_id, start, end)
        cats = [b.category for b in bottlenecks]
        assert "REVIEW" in cats
        review = next(b for b in bottlenecks if b.category == "REVIEW")
        assert review.severity == "HIGH"
    finally:
        db.rollback()
        db.close()


def test_detect_bottlenecks_ci_duration_up():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["pipeline_duration"])
        start, end = _period()
        _add_value(db, team_id, "pipeline_duration", 600.0, start, end, change_pct=15.0)
        db.commit()

        engine = DetectionEngine(db)
        bottlenecks = engine.detect_bottlenecks(team_id, start, end)
        assert any(b.category == "CI" for b in bottlenecks)
    finally:
        db.rollback()
        db.close()


def test_detect_bottlenecks_ci_success_down():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["build_success_rate"])
        start, end = _period()
        _add_value(
            db, team_id, "build_success_rate", 70.0, start, end, change_pct=-15.0
        )
        db.commit()

        engine = DetectionEngine(db)
        bottlenecks = engine.detect_bottlenecks(team_id, start, end)
        assert any(b.category == "CI" for b in bottlenecks)
    finally:
        db.rollback()
        db.close()


def test_detect_bottlenecks_deployment_category():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["deployment_failure_rate"])
        start, end = _period()
        _add_value(
            db, team_id, "deployment_failure_rate", 15.0, start, end, change_pct=20.0
        )
        db.commit()

        engine = DetectionEngine(db)
        bottlenecks = engine.detect_bottlenecks(team_id, start, end)
        assert any(b.category == "DEPLOYMENT" for b in bottlenecks)
    finally:
        db.rollback()
        db.close()


def test_detect_bottlenecks_workflow_category():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["work_in_progress", "cycle_time"])
        start, end = _period()
        _add_value(db, team_id, "work_in_progress", 25.0, start, end, change_pct=15.0)
        _add_value(db, team_id, "cycle_time", 7200.0, start, end, change_pct=12.0)
        db.commit()

        engine = DetectionEngine(db)
        bottlenecks = engine.detect_bottlenecks(team_id, start, end)
        assert any(b.category == "WORKFLOW" for b in bottlenecks)
    finally:
        db.rollback()
        db.close()


def test_detect_bottlenecks_none_when_flat():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["review_backlog", "review_turnaround", "pipeline_duration"])
        start, end = _period()
        _add_value(db, team_id, "review_backlog", 30.0, start, end, change_pct=5.0)
        _add_value(db, team_id, "review_turnaround", 7200.0, start, end, change_pct=5.0)
        _add_value(db, team_id, "pipeline_duration", 600.0, start, end, change_pct=5.0)
        db.commit()

        engine = DetectionEngine(db)
        bottlenecks = engine.detect_bottlenecks(team_id, start, end)
        assert bottlenecks == []
    finally:
        db.rollback()
        db.close()


def test_run_detection_for_period_returns_counts():
    db = SessionLocal()
    try:
        _, team_id = _setup_org_team(db)
        _ensure_defs(db, ["review_backlog", "review_turnaround"])
        start, end = _period()
        _add_value(db, team_id, "review_backlog", 30.0, start, end, change_pct=20.0)
        _add_value(
            db, team_id, "review_turnaround", 7200.0, start, end, change_pct=15.0
        )
        db.commit()

        engine = DetectionEngine(db)
        result = engine.run_detection_for_period(team_id, start, end)
        assert "anomalies_detected" in result
        assert "bottlenecks_detected" in result
        assert result["bottlenecks_detected"] >= 1
    finally:
        db.rollback()
        db.close()


def test_detection_unknown_team_returns_empty():
    db = SessionLocal()
    try:
        engine = DetectionEngine(db)
        assert (
            engine.detect_anomalies(
                uuid.uuid4(), datetime.now(timezone.utc), datetime.now(timezone.utc)
            )
            == []
        )
        assert (
            engine.detect_bottlenecks(
                uuid.uuid4(), datetime.now(timezone.utc), datetime.now(timezone.utc)
            )
            == []
        )
    finally:
        db.rollback()
        db.close()
