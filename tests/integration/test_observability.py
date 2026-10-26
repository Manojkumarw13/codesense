from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_metrics_endpoint_exposes_http_metrics():
    client.get("/api/v1/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "http_requests_total" in body or "http_request_duration_seconds" in body
