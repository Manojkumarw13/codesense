import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.raw import ProviderEvent

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_events():
    """Clean database raw events table before and after each test."""
    db = SessionLocal()
    try:
        db.query(ProviderEvent).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(ProviderEvent).delete()
        db.commit()
    finally:
        db.close()


def test_ingest_single_event_success():
    """Verify that a single valid raw provider event is successfully ingested."""
    event_id = f"test-event-{uuid.uuid4()}"
    payload = {
        "provider": "github",
        "external_event_id": event_id,
        "event_type": "pull_request.opened",
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {"action": "opened", "number": 123},
        "source": "webhook"
    }
    
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ingested"
    assert data["provider"] == "github"
    assert data["external_event_id"] == event_id
    assert "id" in data


def test_ingest_event_deduplication():
    """Verify that posting the duplicate event (same provider & external_event_id) returns ignored_duplicate status."""
    event_id = f"test-event-{uuid.uuid4()}"
    payload = {
        "provider": "github",
        "external_event_id": event_id,
        "event_type": "pull_request.opened",
        "payload": {"action": "opened"},
        "source": "webhook"
    }
    
    # First ingest
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    first_id = response.json()["id"]
    
    # Second ingest (duplicate)
    response2 = client.post("/api/v1/events", json=payload)
    assert response2.status_code == 201
    data2 = response2.json()
    assert data2["status"] == "ignored_duplicate"
    assert data2["id"] == first_id


def test_ingest_event_validation_error():
    """Verify that invalid payloads (empty or missing fields) trigger 422 validation errors."""
    # 1. Missing external_event_id
    payload = {
        "provider": "github",
        "event_type": "pull_request.opened",
        "payload": {"action": "opened"},
        "source": "webhook"
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422
    assert "VALIDATION_FAILED" in response.json()["error"]["code"]
    
    # 2. Empty string provider
    payload2 = {
        "provider": "   ",
        "external_event_id": "event-1",
        "event_type": "pull_request.opened",
        "payload": {"action": "opened"},
        "source": "webhook"
    }
    response2 = client.post("/api/v1/events", json=payload2)
    assert response2.status_code == 422


def test_ingest_batch_success():
    """Verify that multiple events can be ingested in a single batch post."""
    id1 = f"batch-event-{uuid.uuid4()}"
    id2 = f"batch-event-{uuid.uuid4()}"
    
    payload = [
        {
            "provider": "github",
            "external_event_id": id1,
            "event_type": "pull_request.opened",
            "payload": {"action": "opened"},
            "source": "webhook"
        },
        {
            "provider": "github",
            "external_event_id": id2,
            "event_type": "pull_request.closed",
            "payload": {"action": "closed"},
            "source": "webhook"
        }
    ]
    
    response = client.post("/api/v1/events/batch", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["ingested_count"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["status"] == "ingested"
    assert data["results"][1]["status"] == "ingested"


def test_list_raw_events():
    """Verify raw events listing endpoint with pagination and filtering works."""
    # Seed events
    id1 = f"list-event-{uuid.uuid4()}"
    id2 = f"list-event-{uuid.uuid4()}"
    
    client.post("/api/v1/events", json={
        "provider": "github-test",
        "external_event_id": id1,
        "event_type": "pr.open",
        "payload": {},
        "source": "webhook"
    })
    
    client.post("/api/v1/events", json={
        "provider": "gitlab-test",
        "external_event_id": id2,
        "event_type": "mr.open",
        "payload": {},
        "source": "webhook"
    })
    
    # List all
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    
    # Filter by provider
    response_filter = client.get("/api/v1/events?provider=github-test")
    assert response_filter.status_code == 200
    data_filter = response_filter.json()
    assert data_filter["total"] == 1
    assert data_filter["items"][0]["external_event_id"] == id1
