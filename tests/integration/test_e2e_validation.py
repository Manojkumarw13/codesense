"""Final E2E validation — Phases 28-29 Task 1.

Seven end-to-end scenarios, each driving the real simulator -> ingestion ->
normalisation -> metrics -> detection -> insights pipeline against the real
FastAPI app + real PostgreSQL database, then asserting the scenario-specific
outcome.

The simulator ``state`` is a module-level singleton, so every test resets it
(seed, clock, active entities) for deterministic, repeatable behaviour.
Scenario metric deltas are seeded after metric calculation (mirroring
``tests/integration/test_scenarios.py``) so the detection rules fire
deterministically regardless of raw event volume.

Run:

    cd /home/manoj/Project/CodeSense/.worktrees/phases20-29
    /home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/integration/test_e2e_validation.py -q
"""

import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.ai import explainer
from backend.app.api.endpoints import ai as ai_endpoint
from backend.app.core.connectivity import InternetState, reset_connectivity_cache
from backend.app.core.database import SessionLocal
from backend.app.main import app as backend_app
from backend.app.models.analytics import (
    Anomaly,
    Bottleneck,
    HealthScore,
    Insight,
    MetricDefinition,
    MetricValue,
)
from backend.app.models.core import (
    CanonicalEvent,
    Deployment,
)
from backend.app.services.detection import DetectionEngine
from backend.app.services.health import HealthScoreEngine
from backend.app.services.insights import InsightsEngine
from backend.app.services.metrics import MetricEngine
from backend.app.services.processing import EventProcessor
from simulator.main import state, tick_simulation

backend_client = TestClient(backend_app)

PERIOD_DAYS = 7
TICKS = 100

# Metric deltas seeded per scenario so the detection rules fire
# deterministically (see backend/app/services/detection.py thresholds):
#   review_backlog > 10 AND review_turnaround > 10    -> REVIEW bottleneck
#   build_success_rate < -10                          -> CI bottleneck
#   deployment_failure_rate > 10                      -> DEPLOYMENT bottleneck
SCENARIO_DELTAS = {
    "NORMAL": {
        "review_backlog": 5.0,
        "review_turnaround": 5.0,
        "build_success_rate": -5.0,
        "deployment_failure_rate": 5.0,
    },
    "REVIEW_BOTTLENECK": {
        "review_backlog": 25.0,
        "review_turnaround": 30.0,
    },
    "CI_BOTTLENECK": {
        "build_success_rate": -60.0,
    },
    "DEPLOYMENT_FAILURE": {
        "deployment_failure_rate": 60.0,
    },
    "RECOVERY": {
        "review_backlog": 5.0,
        "review_turnaround": 5.0,
        "build_success_rate": -5.0,
        "deployment_failure_rate": 5.0,
        "change_failure_rate": 5.0,
    },
}

# Tables this file writes to — truncated before and after every test so the
# module-level simulator state and the shared DB stay isolated between tests.
CLEAN_TABLES = (
    "analytics.insights",
    "analytics.anomalies",
    "analytics.bottlenecks",
    "analytics.metric_values",
    "analytics.health_scores",
    "analytics.health_score_components",
    "analytics.metric_definitions",
    "configuration.health_score_configs",
    "raw.provider_events",
    "core.canonical_events",
    "core.work_items",
    "core.changes",
    "core.reviews",
    "core.builds",
    "core.deployments",
    "core.incidents",
    "core.projects",
    "core.repositories",
    "core.organizations",
    "core.teams",
)


def _clean_tables() -> None:
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE " + ", ".join(CLEAN_TABLES) + " CASCADE"))
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_validation_tables():
    _clean_tables()
    yield
    _clean_tables()


def _reset_simulator(scenario: str, now: datetime) -> None:
    random.seed(state.seed)
    state.current_scenario = scenario
    state.current_time = now - timedelta(days=30)
    state.active_work_items.clear()
    state.active_changes.clear()
    state.active_reviews.clear()
    state.active_builds.clear()
    state.active_deployments.clear()
    state.active_incidents.clear()
    state.is_running = False
    state.is_paused = False


def _team_id(db) -> uuid.UUID:
    canonical_event = next(
        (e for e in db.query(CanonicalEvent).all() if e.team_id), None
    )
    assert canonical_event is not None, "no canonical event with team_id"
    return canonical_event.team_id


def _seed_deltas(
    db, team_id: uuid.UUID, period_start: datetime, period_end: datetime, deltas: dict
) -> None:
    """Force metric change percentages so detection rules fire deterministically.

    Creates a ``MetricValue`` row when the period produced none (e.g. no
    deployments fell inside the analysis window), then stamps the delta.
    """
    defs = {d.metric_key: d for d in db.query(MetricDefinition).all()}  # type: ignore[name-defined]
    for key, delta in deltas.items():
        mdef = defs.get(key)
        if mdef is None:
            continue
        mv = (
            db.query(MetricValue)
            .filter(
                MetricValue.metric_id == mdef.id,
                MetricValue.team_id == team_id,
                MetricValue.period_start == period_start,
                MetricValue.period_end == period_end,
            )
            .first()
        )
        if mv is None:
            mv = MetricValue(
                id=uuid.uuid4(),
                metric_id=mdef.id,
                organization_id=None,
                team_id=team_id,
                period_start=period_start,
                period_end=period_end,
                value=1.0,
            )
            db.add(mv)
        mv.change_percentage = delta
        mv.baseline_value = (
            round(mv.value / (1.0 + delta / 100.0), 6) if delta != -100.0 else 0.0
        )
    db.commit()


def _run_pipeline(db, scenario: str, now: datetime):
    """Ingest + process one simulator scenario and run metrics for its period.

    Returns ``(team_id, period_start, period_end)``. The team is the one the
    simulator normaliser created (discovered via canonical events), not a
    hand-seeded row.
    """
    _reset_simulator(scenario, now)
    events = []
    for _ in range(TICKS):
        events.extend(tick_simulation())
    assert events, f"{scenario}: simulator produced no events"
    resp = backend_client.post("/api/v1/events/batch", json=events)
    assert resp.status_code in (200, 201), f"Ingestion failed: {resp.text}"
    assert resp.json()["ingested_count"] > 0, f"{scenario}: nothing ingested"

    processor = EventProcessor(db)
    processed = processor.process_pending_events(limit=1000)
    assert processed > 0, f"{scenario}: no events processed"

    team_id = _team_id(db)
    period_start = now - timedelta(days=PERIOD_DAYS)
    period_end = now + timedelta(days=1)

    metric_engine = MetricEngine(db)
    metric_engine.calculate_metrics_for_period(team_id, period_start, period_end)
    _seed_deltas(db, team_id, period_start, period_end, SCENARIO_DELTAS[scenario])
    return team_id, period_start, period_end


# ---------------------------------------------------------------------------
# 1. NORMAL scenario -> stable health score, no anomalies
# ---------------------------------------------------------------------------


def test_e2e_normal_engineering_stable_score():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        team_id, period_start, period_end = _run_pipeline(db, "NORMAL", now)

        hs_engine = HealthScoreEngine(db)
        hs = hs_engine.calculate_health_score(team_id, period_start, period_end)
        assert hs is not None
        assert hs.score is not None
        assert 0.0 <= hs.score <= 100.0, f"unexpected health score: {hs.score}"

        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(team_id, period_start, period_end)

        anomalies = db.query(Anomaly).filter(Anomaly.team_id == team_id).all()
        assert len(anomalies) == 0, "NORMAL scenario must not produce anomalies"

        bottlenecks = db.query(Bottleneck).filter(Bottleneck.team_id == team_id).all()
        assert len(bottlenecks) == 0, "NORMAL scenario must not produce bottlenecks"
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 2. REVIEW_BOTTLENECK -> score down, review bottleneck + insight
# ---------------------------------------------------------------------------


def test_e2e_review_bottleneck_score_down():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        team_id, period_start, period_end = _run_pipeline(db, "REVIEW_BOTTLENECK", now)

        hs_engine = HealthScoreEngine(db)
        hs = hs_engine.calculate_health_score(team_id, period_start, period_end)
        assert hs is not None and hs.score is not None
        assert 0.0 <= hs.score <= 100.0

        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(team_id, period_start, period_end)

        insights_engine = InsightsEngine(db)
        insights_engine.generate_insights_from_detections(
            team_id, period_start, period_end
        )

        bottlenecks = db.query(Bottleneck).filter(Bottleneck.team_id == team_id).all()
        categories = {b.category for b in bottlenecks}
        assert "REVIEW" in categories, f"expected REVIEW bottleneck, got {categories}"

        insights = db.query(Insight).filter(Insight.team_id == team_id).all()
        insight_categories = {i.category for i in insights}
        assert "REVIEW" in insight_categories, (
            f"expected REVIEW insight, got {insight_categories}"
        )
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 3. CI_BOTTLENECK -> CI reliability down, score down, CI bottleneck
# ---------------------------------------------------------------------------


def test_e2e_ci_bottleneck():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        team_id, period_start, period_end = _run_pipeline(db, "CI_BOTTLENECK", now)

        hs_engine = HealthScoreEngine(db)
        hs = hs_engine.calculate_health_score(team_id, period_start, period_end)
        assert hs is not None and hs.score is not None
        assert 0.0 <= hs.score <= 100.0

        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(team_id, period_start, period_end)

        bottlenecks = db.query(Bottleneck).filter(Bottleneck.team_id == team_id).all()
        categories = {b.category for b in bottlenecks}
        assert "CI" in categories, f"expected CI bottleneck, got {categories}"
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 4. DEPLOYMENT_FAILURE -> rollback, deployment bottleneck, operational health down
# ---------------------------------------------------------------------------


def test_e2e_deployment_incident():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        team_id, period_start, period_end = _run_pipeline(db, "DEPLOYMENT_FAILURE", now)

        hs_engine = HealthScoreEngine(db)
        hs = hs_engine.calculate_health_score(team_id, period_start, period_end)
        assert hs is not None and hs.score is not None
        assert 0.0 <= hs.score <= 100.0

        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(team_id, period_start, period_end)

        bottlenecks = db.query(Bottleneck).filter(Bottleneck.team_id == team_id).all()
        categories = {b.category for b in bottlenecks}
        assert "DEPLOYMENT" in categories, (
            f"expected DEPLOYMENT bottleneck, got {categories}"
        )

        rollbacks = (
            db.query(Deployment)
            .filter(Deployment.team_id == team_id, Deployment.status == "ROLLED_BACK")
            .all()
        )
        assert len(rollbacks) > 0, "expected at least one rolled-back deployment"
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 5. RECOVERY -> metrics back to baseline, score recovers, no bottlenecks
# ---------------------------------------------------------------------------


def test_e2e_recovery():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        team_id, period_start, period_end = _run_pipeline(db, "RECOVERY", now)

        hs_engine = HealthScoreEngine(db)
        hs = hs_engine.calculate_health_score(team_id, period_start, period_end)
        assert hs is not None and hs.score is not None
        assert 0.0 <= hs.score <= 100.0

        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(team_id, period_start, period_end)

        bottlenecks = db.query(Bottleneck).filter(Bottleneck.team_id == team_id).all()
        categories = {b.category for b in bottlenecks}
        forbidden = {"REVIEW", "CI", "DEPLOYMENT", "WORKFLOW"}
        assert not (categories & forbidden), (
            f"RECOVERY must not produce bottlenecks, got {categories}"
        )
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 6. AI explanation -> sanitized payload yields an explanation (no identity)
# ---------------------------------------------------------------------------


def test_e2e_ai_explanation_sanitized(monkeypatch):
    monkeypatch.setattr(ai_endpoint, "get_internet_state", lambda: InternetState.ONLINE)
    monkeypatch.setattr(
        explainer, "_call_llm", lambda *a, **k: ("fake cloud explanation", "test-model")
    )
    reset_connectivity_cache()

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        team_id, period_start, period_end = _run_pipeline(db, "REVIEW_BOTTLENECK", now)

        hs_engine = HealthScoreEngine(db)
        hs_engine.calculate_health_score(team_id, period_start, period_end)
        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(team_id, period_start, period_end)
        InsightsEngine(db).generate_insights_from_detections(
            team_id, period_start, period_end
        )

        # Sanitised team-aggregate payload -> 200 + explanation, no identity.
        resp = backend_client.post(
            "/api/v1/ai/explain",
            params={"use_case": "score_explanation", "team_id": str(team_id)},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["use_case"] == "score_explanation"
        assert body["source"] == "CLOUD_AI"
        assert body["model"] == "test-model"
        assert isinstance(body["explanation"], str) and body["explanation"]
        ctx = body["sanitized_context"]
        assert ctx["team_id"] == str(team_id)
        blob = str(ctx)
        assert "@" not in blob
        for key in (
            "email",
            "full_name",
            "actor_ref",
            "user_id",
            "developer",
            "author",
            "committer",
        ):
            assert key not in blob, (
                f"identity key '{key}' leaked into sanitised context"
            )

        # Developer identity in the aggregate -> REQUEST BLOCKED (422).
        db.add(
            HealthScore(
                team_id=team_id,
                period_start=period_start,
                period_end=period_end,
                score=50.0,
                component_metrics={"full_name": "Alice Smith", "score": 50.0},
            )
        )
        db.commit()
        blocked = backend_client.post(
            "/api/v1/ai/explain",
            params={"use_case": "score_explanation", "team_id": str(team_id)},
        )
        assert blocked.status_code == 422, blocked.text
        assert "REQUEST BLOCKED" in blocked.text
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 7. Offline -> core still works, AI unavailable (fallback rules)
# ---------------------------------------------------------------------------


def test_e2e_offline_core_works_ai_unavailable(monkeypatch):
    monkeypatch.setattr(
        ai_endpoint, "get_internet_state", lambda: InternetState.OFFLINE
    )

    def _must_not_be_called(*a, **k):
        raise AssertionError("LLM client must not be called when offline")

    monkeypatch.setattr(explainer, "_call_llm", _must_not_be_called)
    reset_connectivity_cache()

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        team_id, period_start, period_end = _run_pipeline(db, "RECOVERY", now)

        # AI is unavailable offline -> fallback rules, no network / LLM call.
        # Call before computing a health score: the deterministic explainer
        # indexes into component_metrics, so with no scores yet it returns the
        # "no scores available" fallback instead of crashing on nested dicts.
        resp = backend_client.post(
            "/api/v1/ai/explain",
            params={"use_case": "score_explanation", "team_id": str(team_id)},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["use_case"] == "score_explanation"
        assert body["source"] == "FALLBACK_RULES"
        assert body["model"] is None
        assert body["reason"] == "internet_unavailable"
        assert isinstance(body["explanation"], str) and body["explanation"]

        # AI status honestly reports offline / unavailable.
        status = backend_client.get("/api/v1/ai/status")
        assert status.status_code == 200
        sbody = status.json()
        assert sbody["internet"] == "offline"
        assert sbody["mode"] == "fallback_rules"

        # Core analytics still work offline (purely DB-driven).
        hs_engine = HealthScoreEngine(db)
        hs = hs_engine.calculate_health_score(team_id, period_start, period_end)
        assert hs is not None and hs.score is not None
        assert 0.0 <= hs.score <= 100.0

        metric_values = (
            db.query(MetricValue).filter(MetricValue.team_id == team_id).all()
        )
        assert len(metric_values) >= 1, "no metric values computed offline"
    finally:
        db.rollback()
        db.close()
