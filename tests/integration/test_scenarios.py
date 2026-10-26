"""Scenario tests (Phase 23 Task 6).

Drives the simulator through each scenario
(NORMAL, REVIEW_BOTTLENECK, CI_BOTTLENECK, DEPLOYMENT_FAILURE, INCIDENT_SPIKE,
RECOVERY), ingests the events, processes them into canonical entities,
calculates metrics, runs detection + insights, and asserts the scenario
produces its expected detections.

Run:

    cd /home/manoj/Project/CodeSense/.worktrees/phases20-29
    /home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/integration/test_scenarios.py -q
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.core.database import SessionLocal
from backend.app.main import app as backend_app
from backend.app.models.analytics import (
    Anomaly,
    Bottleneck,
    Insight,
    MetricDefinition,
    MetricValue,
)
from backend.app.models.core import CanonicalEvent, Team
from backend.app.services.detection import DetectionEngine
from backend.app.services.insights import InsightsEngine
from backend.app.services.metrics import MetricEngine
from backend.app.services.processing import EventProcessor
from simulator.main import state, tick_simulation

backend_client = TestClient(backend_app)

PERIOD_DAYS = 7
TICKS = 200

# Metric deltas seeded per scenario so the detection rules fire
# deterministically. Detection thresholds (backend/app/services/detection.py):
#   review_backlog > 10 AND review_turnaround > 10          -> REVIEW bottleneck
#   build_success_rate < -10                                -> CI bottleneck
#   deployment_failure_rate > 10                            -> DEPLOYMENT bottleneck
#   |change_percentage| > 50                                -> anomaly (fallback)
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
    "INCIDENT_SPIKE": {
        "change_failure_rate": 80.0,
    },
    "RECOVERY": {
        "review_backlog": 5.0,
        "review_turnaround": 5.0,
        "build_success_rate": -5.0,
        "deployment_failure_rate": 5.0,
        "change_failure_rate": 5.0,
    },
}

# Expected detections per scenario.
SCENARIO_EXPECTATIONS = {
    "NORMAL": {
        "forbidden_bottlenecks": {"REVIEW", "CI", "DEPLOYMENT", "WORKFLOW"},
        "max_anomalies": 0,
    },
    "REVIEW_BOTTLENECK": {
        "required_bottlenecks": {"REVIEW"},
        "required_insights": {"REVIEW"},
    },
    "CI_BOTTLENECK": {
        "required_bottlenecks": {"CI"},
    },
    "DEPLOYMENT_FAILURE": {
        "required_bottlenecks": {"DEPLOYMENT"},
    },
    "INCIDENT_SPIKE": {
        "min_anomalies": 1,
    },
    "RECOVERY": {
        "forbidden_bottlenecks": {"REVIEW", "CI", "DEPLOYMENT", "WORKFLOW"},
    },
}

# Tables conftest does NOT truncate between tests that this file writes to.
CLEAN_TABLES = (
    "analytics.insights",
    "analytics.anomalies",
    "analytics.bottlenecks",
    "analytics.metric_values",
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
)


def _clean_tables() -> None:
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE " + ", ".join(CLEAN_TABLES) + " CASCADE"))
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_scenario_tables():
    _clean_tables()
    yield
    _clean_tables()


def _reset_simulator(scenario: str, now: datetime) -> None:
    random.seed(state.seed)
    state.current_scenario = scenario
    state.current_time = now - timedelta(days=PERIOD_DAYS)
    state.active_work_items.clear()
    state.active_changes.clear()
    state.active_reviews.clear()
    state.active_builds.clear()
    state.active_deployments.clear()
    state.active_incidents.clear()
    state.is_running = False
    state.is_paused = False


def _ingest_scenario(scenario: str, now: datetime) -> None:
    _reset_simulator(scenario, now)
    events = []
    for _ in range(TICKS):
        events.extend(tick_simulation())
    assert events, f"{scenario}: simulator produced no events"
    response = backend_client.post("/api/v1/events/batch", json=events)
    assert response.status_code in (200, 201), response.text
    assert response.json()["ingested_count"] > 0, f"{scenario}: nothing ingested"


def _team_id(db) -> uuid.UUID:
    canonical_event = next(
        (e for e in db.query(CanonicalEvent).all() if e.team_id), None
    )
    assert canonical_event is not None, "no canonical event with team_id"
    return canonical_event.team_id


def _seed_deltas(db, team_id, org_id, period_start, period_end, deltas) -> None:
    defs = {d.metric_key: d for d in db.query(MetricDefinition).all()}
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
                organization_id=org_id,
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
    _ingest_scenario(scenario, now)
    processor = EventProcessor(db)
    processor.process_pending_events(limit=1000)
    team_id = _team_id(db)
    team = db.query(Team).get(team_id)
    org_id = team.organization_id
    period_start = now - timedelta(days=PERIOD_DAYS)
    period_end = now + timedelta(days=1)
    metric_engine = MetricEngine(db)
    metric_engine.calculate_metrics_for_period(team_id, period_start, period_end)
    _seed_deltas(
        db, team_id, org_id, period_start, period_end, SCENARIO_DELTAS[scenario]
    )
    return db, team_id, period_start, period_end


@pytest.mark.parametrize("scenario", list(SCENARIO_DELTAS))
def test_scenario_produces_expected_detection(scenario):
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        db, team_id, period_start, period_end = _run_pipeline(db, scenario, now)

        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(team_id, period_start, period_end)

        insights_engine = InsightsEngine(db)
        insights_engine.generate_insights_from_detections(
            team_id, period_start, period_end
        )

        expectations = SCENARIO_EXPECTATIONS[scenario]

        bottlenecks = (
            db.query(Bottleneck)
            .filter(
                Bottleneck.team_id == team_id,
                Bottleneck.detected_at >= period_start,
                Bottleneck.detected_at <= period_end,
            )
            .all()
        )
        bottleneck_categories = {b.category for b in bottlenecks}

        anomalies = (
            db.query(Anomaly)
            .filter(
                Anomaly.team_id == team_id,
                Anomaly.detected_at >= period_start,
                Anomaly.detected_at <= period_end,
            )
            .all()
        )

        if "required_bottlenecks" in expectations:
            missing = expectations["required_bottlenecks"] - bottleneck_categories
            assert not missing, (
                f"{scenario}: expected bottlenecks {expectations['required_bottlenecks']}, "
                f"got {bottleneck_categories}"
            )
        if "required_insights" in expectations:
            insights = db.query(Insight).filter(Insight.team_id == team_id).all()
            insight_categories = {i.category for i in insights}
            missing = expectations["required_insights"] - insight_categories
            assert not missing, (
                f"{scenario}: expected insights {expectations['required_insights']}, "
                f"got {insight_categories}"
            )
        if "min_anomalies" in expectations:
            assert len(anomalies) >= expectations["min_anomalies"], (
                f"{scenario}: expected >= {expectations['min_anomalies']} anomalies, got {len(anomalies)}"
            )
        if "max_anomalies" in expectations:
            assert len(anomalies) <= expectations["max_anomalies"], (
                f"{scenario}: expected <= {expectations['max_anomalies']} anomalies, got {len(anomalies)}"
            )
        if "forbidden_bottlenecks" in expectations:
            present = bottleneck_categories & expectations["forbidden_bottlenecks"]
            assert not present, f"{scenario}: unexpected bottlenecks {present}"
    finally:
        db.rollback()
        db.close()
