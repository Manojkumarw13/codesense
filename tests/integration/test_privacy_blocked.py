"""Phase 23 Task 4: privacy test — identity → REQUEST BLOCKED (422), sanitized → 200.

Asserts the AI privacy gateway blocks developer identity (name / email / ID /
individual metrics) and that sanitized team-aggregate data flows through
``POST /api/v1/ai/explain`` with a 200.

Integration-style: real TestClient against the real app + real PostgreSQL DB.
The LLM seam and the connectivity probe are monkeypatched so no network is
ever touched. Production seams (`backend/app/api/endpoints/ai.py`,
`backend/app/privacy/gateway.py`, `backend/app/core/database.py`) are read-only
and untouched — this file only adds tests.

Run:
    cd /home/manoj/Project/CodeSense/.worktrees/phases20-29
    /home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/integration/test_privacy_blocked.py -q
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.ai import explainer
from backend.app.api.endpoints import ai as ai_endpoint
from backend.app.core.connectivity import InternetState
from backend.app.core.database import SessionLocal, get_db
from backend.app.models.analytics import HealthScore
from backend.app.models.core import Organization, Team
from backend.app.privacy.gateway import PrivacyBlockedError, PrivacyGateway

# ---------------------------------------------------------------------------
# DB session fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.execute(text("DELETE FROM analytics.health_scores"))
        db.commit()
        db.close()


# ---------------------------------------------------------------------------
# Privacy gateway (direct): identity → REQUEST BLOCKED
# ---------------------------------------------------------------------------


def test_gateway_blocks_name():
    with pytest.raises(PrivacyBlockedError, match="REQUEST BLOCKED"):
        PrivacyGateway().sanitize({"full_name": "Alice Smith", "score": 85.0})


def test_gateway_blocks_email():
    with pytest.raises(PrivacyBlockedError, match="REQUEST BLOCKED"):
        PrivacyGateway().sanitize({"email": "alice@example.com", "score": 85.0})


def test_gateway_blocks_id():
    with pytest.raises(PrivacyBlockedError, match="REQUEST BLOCKED"):
        PrivacyGateway().sanitize(
            {"user_id": "550e8400-e29b-41d4-a716-446655440000", "score": 85.0}
        )


def test_gateway_blocks_individual_metrics():
    # Per-developer metric attributed to an author carries identity.
    with pytest.raises(PrivacyBlockedError, match="REQUEST BLOCKED"):
        PrivacyGateway().sanitize({"author": "Alice Smith", "commits": 42})


def test_gateway_passes_team_aggregates():
    context = {
        "team_id": "team-alpha",
        "health_scores": [{"score": 82.5, "component_metrics": {"code_quality": 90.0}}],
        "insights": [],
        "anomalies": [],
        "bottlenecks": [],
    }
    assert PrivacyGateway().sanitize(context) == context


# ---------------------------------------------------------------------------
# Endpoint seam: POST /api/v1/ai/explain
# ---------------------------------------------------------------------------


def _seed_team(db, name="Privacy Test Team"):
    org_id = uuid.uuid4()
    team_id = uuid.uuid4()
    org = Organization(id=org_id, name="Privacy Test Org")
    team = Team(id=team_id, name=name, organization_id=org_id)
    db.add_all([org, team])
    db.commit()
    return team


def _seed_health_score(db, team_id, component_metrics):
    now = datetime.now(timezone.utc)
    db.add(
        HealthScore(
            team_id=team_id,
            period_start=now - timedelta(days=7),
            period_end=now,
            score=85.0,
            component_metrics=component_metrics,
        )
    )
    db.commit()


def _build_client(monkeypatch):
    """App with the AI router, a real per-request DB session, internet forced
    ONLINE (so the privacy-gated ``explain`` path runs) and the LLM seam
    stubbed (no network)."""
    app = FastAPI()
    app.include_router(ai_endpoint.router, prefix="/api/v1")

    def _override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(ai_endpoint, "get_internet_state", lambda: InternetState.ONLINE)
    monkeypatch.setattr(
        explainer, "_call_llm", lambda *a, **k: ("fake explanation", "test-model")
    )
    return TestClient(app, raise_server_exceptions=False)


def test_endpoint_sanitized_team_aggregate_returns_200(monkeypatch, db):
    team = _seed_team(db)
    _seed_health_score(db, team.id, {"code_quality": 90.0, "delivery_flow": 80.0})

    client = _build_client(monkeypatch)
    resp = client.post(
        "/api/v1/ai/explain",
        params={"use_case": "score_explanation", "team_id": str(team.id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["source"] == "CLOUD_AI"
    assert body["sanitized_context"]["team_id"] == str(team.id)
    assert len(body["sanitized_context"]["health_scores"]) == 1


def test_endpoint_identity_in_aggregate_returns_422(monkeypatch, db):
    team = _seed_team(db)
    _seed_health_score(db, team.id, {"full_name": "Alice Smith", "code_quality": 90.0})

    client = _build_client(monkeypatch)
    resp = client.post(
        "/api/v1/ai/explain",
        params={"use_case": "score_explanation", "team_id": str(team.id)},
    )
    assert resp.status_code == 422, resp.text
    assert "REQUEST BLOCKED" in resp.json()["detail"]
