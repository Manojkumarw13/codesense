"""Phase 23 Task 5 — Offline mode: core OK, AI unavailable.

With the connectivity probe forced OFFLINE:
  * ``GET /api/v1/health``   -> 200, ``mode: "offline"``
  * metrics / health-score engines still run (purely DB, no network)
  * ``GET /api/v1/ai/status`` -> ``configured: false``
  * ``POST /api/v1/ai/explain`` -> ``source: FALLBACK_RULES``, no network/LLM call

No test here touches the public internet: the probe is monkeypatched in the
endpoint namespaces (the endpoints import ``get_internet_state`` directly, so
patching ``backend.app.core.connectivity`` alone would not reach them), and
the LLM client is stubbed so any network attempt fails the test loudly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.core.connectivity import InternetState, reset_connectivity_cache
from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.analytics import HealthScore, MetricValue
from backend.app.models.core import Organization, Team
from backend.app.services.health import HealthScoreEngine
from backend.app.services.metrics import MetricEngine

client = TestClient(app)


def _force_offline(monkeypatch):
    """Make every endpoint observe the connectivity probe as OFFLINE.

    ``health`` and ``ai`` import ``get_internet_state`` into their own module
    namespace, so the probe must be patched there (the core cache is cleared
    too so no stale ONLINE state can leak between tests).
    """
    monkeypatch.setattr(
        "backend.app.api.endpoints.health.get_internet_state",
        lambda: InternetState.OFFLINE,
    )
    monkeypatch.setattr(
        "backend.app.api.endpoints.ai.get_internet_state",
        lambda: InternetState.OFFLINE,
    )
    reset_connectivity_cache()


@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _cleanup_analytics(db):
    """Delete rows this file seeds so tests stay isolated."""
    yield
    db.execute(text("DELETE FROM analytics.health_score_components"))
    db.execute(text("DELETE FROM analytics.health_scores"))
    db.execute(text("DELETE FROM analytics.metric_values"))
    db.execute(text("DELETE FROM analytics.metric_definitions"))
    db.execute(text("DELETE FROM configuration.health_score_configs"))
    db.execute(text("DELETE FROM core.teams"))
    db.execute(text("DELETE FROM core.organizations"))
    db.commit()


def test_health_reports_offline_mode(monkeypatch):
    _force_offline(monkeypatch)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["internet"] == "offline"
    assert data["mode"] == "offline"
    assert data["ai_available"] is False


def test_ai_status_configured_false_when_offline(monkeypatch):
    _force_offline(monkeypatch)
    # A key *is* configured, so online would report configured: true —
    # offline must still report configured: false.
    monkeypatch.setattr(
        "backend.app.core.settings.settings.OPENROUTER_API_KEY",
        "sk-test-offline-key",
    )
    resp = client.get("/api/v1/ai/status")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["configured"] is False
    assert data["mode"] == "fallback_rules"
    assert data["internet"] == "offline"
    assert data["reason"] == "internet_unavailable"


def test_ai_explain_uses_fallback_rules_without_network(monkeypatch):
    _force_offline(monkeypatch)

    def _must_not_be_called(*args, **kwargs):
        raise AssertionError("LLM client must not be called when offline")

    monkeypatch.setattr("backend.app.ai.client.complete", _must_not_be_called)

    resp = client.post("/api/v1/ai/explain", params={"use_case": "score_explanation"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["use_case"] == "score_explanation"
    assert data["source"] == "FALLBACK_RULES"
    assert data["model"] is None
    assert data["reason"] == "internet_unavailable"
    assert isinstance(data["explanation"], str) and data["explanation"]


def test_metrics_and_health_score_still_work_offline(db, monkeypatch):
    _force_offline(monkeypatch)

    org_id = uuid.uuid4()
    team_id = uuid.uuid4()
    db.add_all(
        [
            Organization(id=org_id, name="Offline Org"),
            Team(id=team_id, name="Offline Team", organization_id=org_id),
        ]
    )
    db.commit()

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    end = now

    # Metrics: the engine reads only DB tables — never the network.
    metric_engine = MetricEngine(db)
    values = metric_engine.calculate_metrics_for_period(team_id, start, end)
    assert len(values) >= 1
    assert all(v.team_id == team_id for v in values)
    assert all(v.period_start == start and v.period_end == end for v in values)
    persisted = db.query(MetricValue).filter(MetricValue.team_id == team_id).all()
    assert len(persisted) == len(values)

    # Health score: computed from the same DB, still offline.
    hs_engine = HealthScoreEngine(db)
    score = hs_engine.calculate_health_score(team_id, start, end)
    assert score.score is not None
    assert score.score >= 0.0
    row = db.query(HealthScore).filter(HealthScore.team_id == team_id).first()
    assert row is not None
    assert row.score == score.score
