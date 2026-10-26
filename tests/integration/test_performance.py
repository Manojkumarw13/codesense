"""Phase 23 Task 7 — performance baselines (measure + record, no thresholds).

Records observed baselines for ingestion rate, API latency (p50/p95),
dashboard load time and analytics latency.  Per the "no flaky thresholds"
constraint, no test asserts a hard performance limit — each test asserts
real behaviour (200 responses, data present) and prints the measured value
so it can be tracked across runs.

No test touches the public internet: the connectivity probe is monkeypatched
to OFFLINE for every endpoint latency measurement.
"""

from __future__ import annotations

import random
import statistics
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.core.connectivity import InternetState, reset_connectivity_cache
from backend.app.core.database import SessionLocal
from backend.app.main import app as backend_app
from backend.app.models.core import Organization, Team
from backend.app.services.health import HealthScoreEngine
from backend.app.services.metrics import MetricEngine
from backend.app.services.processing import EventProcessor
from simulator.main import state, tick_simulation

backend_client = TestClient(backend_app)

# Public endpoints that feed the dashboard shell; none require authentication.
_DASHBOARD_ENDPOINTS = (
    "/api/v1/health",
    "/api/v1/events",
    "/api/v1/metrics",
    "/api/v1/providers",
)

# Tables this file writes; the shared conftest only truncates core tables.
_CLEAN_TABLES = (
    "raw.provider_events",
    "analytics.metric_values",
    "analytics.metric_definitions",
    "analytics.health_scores",
    "analytics.health_score_components",
    "analytics.anomalies",
    "analytics.bottlenecks",
    "analytics.insights",
    "analytics.analytics_snapshots",
)


def _percentile(values: list[float], p: float) -> float:
    """Linear-interpolation percentile (0-100) of ``values``."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * (p / 100.0)
    lower = int(k)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (k - lower)


def _seed_simulator() -> None:
    """Reset simulator state deterministically (mirrors the fixed e2e test)."""
    random.seed(state.seed)
    state.current_scenario = "NORMAL"
    state.current_time = datetime.now(timezone.utc) - timedelta(days=30)
    state.active_work_items.clear()
    state.active_changes.clear()
    state.active_reviews.clear()
    state.active_builds.clear()
    state.active_deployments.clear()
    state.active_incidents.clear()
    state.is_running = False
    state.is_paused = False


def _collect_events(count: int = 40) -> list:
    """Run the simulator until at least ``count`` events are produced."""
    events: list = []
    for _ in range(400):
        events.extend(tick_simulation())
        if len(events) >= count:
            break
    return events[:count]


@pytest.fixture(autouse=True)
def _clean_raw_and_analytics():
    """Truncate raw + analytics tables after every test for isolation."""
    yield
    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE " + ", ".join(_CLEAN_TABLES) + " CASCADE"))
        db.commit()
    finally:
        db.close()


def _offline_health_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.app.api.endpoints.health.get_internet_state",
        lambda: InternetState.OFFLINE,
    )
    reset_connectivity_cache()


# ---------------------------------------------------------------------------
# Ingestion rate
# ---------------------------------------------------------------------------


def test_ingestion_rate_records_baseline():
    _seed_simulator()
    events = _collect_events(count=60)
    assert events, "Simulator produced no events"

    start = time.perf_counter()
    response = backend_client.post("/api/v1/events/batch", json=events)
    elapsed = time.perf_counter() - start

    assert response.status_code in (200, 201), response.text
    ingested = response.json()["ingested_count"]
    assert ingested > 0, "No events were ingested"

    rate = ingested / elapsed if elapsed > 0 else float("inf")
    print(
        f"\n[baseline] ingestion_rate: {rate:.1f} events/sec "
        f"({ingested} events in {elapsed:.3f}s)"
    )


# ---------------------------------------------------------------------------
# API latency p50/p95
# ---------------------------------------------------------------------------


def test_api_latency_percentiles_record_baseline(
    monkeypatch: pytest.MonkeyPatch,
):
    _offline_health_probe(monkeypatch)

    iterations = 30
    latencies: dict[str, list[float]] = {ep: [] for ep in _DASHBOARD_ENDPOINTS}
    for _ in range(iterations):
        for ep in _DASHBOARD_ENDPOINTS:
            t0 = time.perf_counter()
            resp = backend_client.get(ep)
            assert resp.status_code == 200, f"{ep}: {resp.text}"
            latencies[ep].append(time.perf_counter() - t0)

    parts = []
    for ep in _DASHBOARD_ENDPOINTS:
        samples = latencies[ep]
        p50 = _percentile(samples, 50)
        p95 = _percentile(samples, 95)
        parts.append(
            f"{ep.split('/')[-1]}: p50={p50 * 1000:.1f}ms p95={p95 * 1000:.1f}ms"
        )
    print("\n[baseline] api_latency: " + " | ".join(parts))


# ---------------------------------------------------------------------------
# Dashboard load time
# ---------------------------------------------------------------------------


def test_dashboard_load_time_records_baseline(
    monkeypatch: pytest.MonkeyPatch,
):
    _offline_health_probe(monkeypatch)

    rounds = 10
    times: list[float] = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        for ep in _DASHBOARD_ENDPOINTS:
            resp = backend_client.get(ep)
            assert resp.status_code == 200, f"{ep}: {resp.text}"
        times.append(time.perf_counter() - t0)

    avg = statistics.mean(times)
    print(
        f"\n[baseline] dashboard_load_time: {avg * 1000:.1f}ms average over {rounds} rounds "
        f"(min={min(times) * 1000:.1f}ms max={max(times) * 1000:.1f}ms)"
    )


# ---------------------------------------------------------------------------
# Analytics latency
# ---------------------------------------------------------------------------


def test_analytics_latency_records_baseline():
    org_id = uuid.uuid4()
    team_id = uuid.uuid4()
    db = SessionLocal()
    try:
        db.add_all(
            [
                Organization(id=org_id, name="Perf Org"),
                Team(id=team_id, name="Perf Team", organization_id=org_id),
            ]
        )
        db.commit()

        _seed_simulator()
        events = _collect_events(count=40)
        backend_client.post("/api/v1/events/batch", json=events)

        processor = EventProcessor(db)
        processor.process_pending_events(limit=500)

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        end = now + timedelta(days=1)

        t0 = time.perf_counter()
        metrics = MetricEngine(db).calculate_metrics_for_period(team_id, start, end)
        score = HealthScoreEngine(db).calculate_health_score(team_id, start, end)
        elapsed = time.perf_counter() - t0

        assert len(metrics) > 0, "Metrics engine produced nothing"
        assert score is not None, "Health score engine produced nothing"
        assert score.score is not None and score.score >= 0

        print(
            f"\n[baseline] analytics_latency: {elapsed * 1000:.1f}ms "
            f"(metrics={len(metrics)}, health_score={score.score})"
        )
    finally:
        db.rollback()
        db.close()
