from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["internet"] in ("online", "offline")
    assert body["mode"] == ("normal" if body["internet"] == "online" else "offline")
    assert isinstance(body["ai_available"], bool)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to CodeSense" in response.json()["message"]
