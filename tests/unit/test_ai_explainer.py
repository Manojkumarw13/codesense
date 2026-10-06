"""Phase 19 tests: privacy gateway blocks identity, explainer falls back, endpoint shapes.

No network, no database: the LLM seam (`_call_llm`) and the DB session are
both faked. Privacy tests assert REQUEST BLOCKED the way Phase 23 will.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.ai import explainer
from backend.app.ai.client import LlmUnavailableError
from backend.app.api.endpoints import ai as ai_endpoint
from backend.app.core.database import get_db
from backend.app.privacy.gateway import PrivacyBlockedError, PrivacyGateway


def make_empty_db() -> MagicMock:
    """Fake Session whose every query returns []."""
    db = MagicMock()
    q = db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.all.return_value = []
    return db


# --- Privacy gateway ---


def test_gateway_blocks_email_string():
    with pytest.raises(PrivacyBlockedError, match="REQUEST BLOCKED"):
        PrivacyGateway().sanitize({"summary": "contact bob@example.com for details"})


def test_gateway_blocks_username_key():
    with pytest.raises(PrivacyBlockedError, match="REQUEST BLOCKED"):
        PrivacyGateway().sanitize({"username": "bob"})


def test_gateway_blocks_actor_ref():
    with pytest.raises(PrivacyBlockedError, match="REQUEST BLOCKED"):
        PrivacyGateway().sanitize({"actor_ref": "some-id"})


def test_gateway_strips_raw_payload_but_passes():
    clean = PrivacyGateway().sanitize(
        {
            "score": 82.5,
            "raw_payload": {"secret": "drop me"},
            "payload": [1, 2, 3],
        }
    )
    assert clean == {"score": 82.5}


def test_gateway_passes_team_aggregates():
    context = {
        "team_id": "team-alpha",
        "health_scores": [{"score": 82.5, "component_metrics": {"delivery_flow": 90.0}}],
        "bottlenecks": [],
    }
    assert PrivacyGateway().sanitize(context) == context


# --- Explainer fallback (no LLM configured -> deterministic) ---


def test_explain_unknown_use_case_rejected():
    with pytest.raises(ValueError, match="Unknown use_case"):
        explainer.explain(make_empty_db(), "nonsense")


def test_explain_falls_back_without_llm(monkeypatch):
    def boom(*args, **kwargs):
        raise LlmUnavailableError("down")

    monkeypatch.setattr(explainer, "_call_llm", boom)
    result = explainer.explain(make_empty_db(), "score_explanation")
    assert result["source"] == "FALLBACK_RULES"
    assert result["model"] is None
    assert "No health scores" in result["explanation"]


def test_explain_uses_llm_text_verbatim(monkeypatch):
    monkeypatch.setattr(explainer, "_call_llm", lambda *a, **k: ("Cloud says hi.", "test-model"))
    result = explainer.explain(make_empty_db(), "trend_summary")
    assert result["source"] == "CLOUD_AI"
    assert result["explanation"] == "Cloud says hi."
    assert result["model"] == "test-model"


def test_fallback_covers_all_use_cases(monkeypatch):
    monkeypatch.setattr(
        explainer, "_call_llm", lambda *a, **k: (_ for _ in ()).throw(LlmUnavailableError("x"))
    )
    for use_case in explainer.USE_CASES:
        result = explainer.explain(make_empty_db(), use_case)
        assert result["explanation"], use_case


# --- Endpoint seam (router only, faked DB + LLM) ---


def build_client(monkeypatch, llm_text: str | None = "Endpoint explanation.") -> TestClient:
    app = FastAPI()
    app.include_router(ai_endpoint.router)
    app.dependency_overrides[get_db] = lambda: make_empty_db()
    if llm_text is None:
        def boom(*args, **kwargs):
            raise LlmUnavailableError("down")

        monkeypatch.setattr(explainer, "_call_llm", boom)
    else:
        monkeypatch.setattr(
            explainer, "_call_llm", lambda *a, **k: (llm_text, "test-model")
        )
    return TestClient(app, raise_server_exceptions=False)


def test_endpoint_returns_cloud_explanation(monkeypatch):
    client = build_client(monkeypatch)
    resp = client.post("/ai/explain", params={"use_case": "score_explanation"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["source"] == "CLOUD_AI"
    assert body["sanitized_context"]["health_scores"] == []


def test_endpoint_falls_back_when_llm_down(monkeypatch):
    client = build_client(monkeypatch, llm_text=None)
    resp = client.post("/ai/explain", params={"use_case": "bottleneck_explanation"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["source"] == "FALLBACK_RULES"


def test_endpoint_rejects_unknown_use_case(monkeypatch):
    client = build_client(monkeypatch)
    resp = client.post("/ai/explain", params={"use_case": "nonsense"})
    assert resp.status_code == 422


def test_status_endpoint_shape():
    app = FastAPI()
    app.include_router(ai_endpoint.router)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/ai/status")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"configured", "model", "mode"}
