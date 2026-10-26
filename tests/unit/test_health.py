from fastapi.testclient import TestClient

from backend.app.api.endpoints import health as health_endpoint
from backend.app.core.connectivity import (
    InternetState,
    reset_connectivity_cache,
)
from backend.app.main import app

client = TestClient(app)


def test_health(monkeypatch):
    reset_connectivity_cache()
    monkeypatch.setattr(
        health_endpoint, "get_internet_state", lambda: InternetState.ONLINE
    )
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["internet"] == "online"
    assert body["mode"] == "normal"
    assert isinstance(body["ai_available"], bool)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to CodeSense" in response.json()["message"]
