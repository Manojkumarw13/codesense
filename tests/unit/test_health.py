from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to CodeSense" in response.json()["message"]

