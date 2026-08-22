import sys
import os
from fastapi.testclient import TestClient

# Add backend directory to sys.path so we can import app
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to CodeSense" in response.json()["message"]
