"""Integration test: Simulator → Ingestion → Raw → Canonical → Analytics → Dashboard.

Drives the full pipeline end-to-end:

    simulator.tick_simulation()
      → POST /api/v1/events/batch            (raw provider events)
      → EventProcessor.process_pending_events() (canonical events + core entities)
      → MetricEngine.calculate_metrics_for_period() (metric values)
      → DetectionEngine.run_detection_for_period()  (anomalies + bottlenecks)
      → HealthScoreEngine.calculate_health_score()  (health score)
      → InsightsEngine.generate_insights_from_detections() (insights)

Asserts that dashboard-relevant data exists: health score, insights,
anomalies and bottlenecks are all present.

Run:

    cd /home/manoj/Project/CodeSense/.worktrees/phases20-29
    /home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/integration/test_pipeline_e2e.py -q
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

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
from backend.app.models.raw import ProviderEvent
from backend.app.services.detection import DetectionEngine
from backend.app.services.health import HealthScoreEngine
from backend.app.services.insights import InsightsEngine
from backend.app.services.metrics import MetricEngine
from backend.app.services.processing import EventProcessor
from simulator.main import state, tick_simulation

backend_client = TestClient(backend_app)

PERIOD_DAYS = 7

# Detection-relevant deltas seeded because there is no previous period, so the
# metric engine leaves ``change_percentage`` as None. These values key the
# detection rules the dashboard depends on (review backlog + turnaround,
# build success rate drop).
_TARGET_DELTAS = {
    "review_backlog": 25.0,
    "review_turnaround": 30.0,
    "build_success_rate": -60.0,
}


@pytest.fixture(autouse=True)
def clean_simulator_events():
    """Remove simulator raw events left over from previous runs so this test
    is idempotent (``conftest`` already truncates core/analytics tables)."""
    db = SessionLocal()
    try:
        db.query(ProviderEvent).filter(ProviderEvent.provider == "simulator").delete()
        db.commit()
    finally:
        db.close()


def test_simulator_ingestion_raw_canonical_analytics_dashboard():
    db = SessionLocal()
    try:
        # --- Deterministic simulator setup ----------------------------------
        random.seed(state.seed)
        state.current_scenario = "REVIEW_BOTTLENECK"
        state.current_time = datetime.now(timezone.utc) - timedelta(days=30)
        state.active_work_items.clear()
        state.active_changes.clear()
        state.active_reviews.clear()
        state.active_builds.clear()
        state.active_deployments.clear()
        state.active_incidents.clear()
        state.is_running = False
        state.is_paused = False

        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=PERIOD_DAYS)
        # Buffer past "now" so detection-time ``detected_at`` timestamps fall
        # inside the period window (mirrors test_e2e_phases.py).
        period_end = now + timedelta(days=1)

        # --- Simulator → Ingestion ------------------------------------------
        events = []
        for _ in range(200):
            events.extend(tick_simulation())
            if len(events) >= 20:
                break
        assert len(events) > 0, "Simulator produced no events"

        response = backend_client.post("/api/v1/events/batch", json=events)
        assert response.status_code in (200, 201), response.text
        assert response.json()["ingested_count"] > 0, "Nothing ingested"

        raw_events = db.query(ProviderEvent).all()
        assert len(raw_events) > 0, "Raw events not persisted"

        # --- Raw → Canonical ------------------------------------------------
        processor = EventProcessor(db)
        processed_count = processor.process_pending_events(limit=500)
        assert processed_count > 0, "Canonical processing processed nothing"

        canonical_events = db.query(CanonicalEvent).all()
        assert len(canonical_events) > 0, "Canonical events not created"

        canonical_event = next(e for e in canonical_events if e.team_id)
        active_team_id = canonical_event.team_id

        # --- Analytics: metrics ---------------------------------------------
        metric_engine = MetricEngine(db)  # ensures metric definitions exist
        metrics = metric_engine.calculate_metrics_for_period(
            active_team_id, period_start, period_end
        )
        assert len(metrics) > 0, "No metrics calculated"

        team = db.query(Team).get(active_team_id)
        org_id = team.organization_id

        # Seed the deltas the detection rules key on so anomalies and
        # bottlenecks are deterministically produced from the pipeline data.
        defs = {d.metric_key: d for d in db.query(MetricDefinition).all()}
        for key, delta in _TARGET_DELTAS.items():
            mdef = defs.get(key)
            if mdef is None:
                continue
            mv = (
                db.query(MetricValue)
                .filter(
                    MetricValue.metric_id == mdef.id,
                    MetricValue.team_id == active_team_id,
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
                    team_id=active_team_id,
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

        # --- Detection ------------------------------------------------------
        detection_engine = DetectionEngine(db)
        detection_engine.run_detection_for_period(
            active_team_id, period_start, period_end
        )

        anomalies = db.query(Anomaly).filter(Anomaly.team_id == active_team_id).all()
        bottlenecks = (
            db.query(Bottleneck).filter(Bottleneck.team_id == active_team_id).all()
        )
        assert len(anomalies) > 0, "No anomalies detected"
        assert len(bottlenecks) > 0, "No bottlenecks detected"

        # --- Health score ---------------------------------------------------
        health_engine = HealthScoreEngine(db)
        health_score = health_engine.calculate_health_score(
            active_team_id, period_start, period_end
        )
        assert health_score is not None, "Health score not calculated"
        assert health_score.score >= 0, "Health score should be non-negative"

        # --- Insights -------------------------------------------------------
        insights_engine = InsightsEngine(db)
        insights = insights_engine.generate_insights_from_detections(
            active_team_id, period_start, period_end
        )
        db_insights = db.query(Insight).filter(Insight.team_id == active_team_id).all()
        assert len(db_insights) == len(insights), (
            "Insights database verification failed"
        )
        assert len(db_insights) > 0, "No insights generated"

        print(
            "Pipeline E2E completed: simulator → ingestion → raw → canonical → "
            "analytics → dashboard"
        )
    finally:
        db.rollback()
        db.close()
