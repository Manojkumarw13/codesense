from fastapi.testclient import TestClient

from simulator.main import app, state

client = TestClient(app)

def test_simulator_status():
    """Verify that the simulator defaults are correct on startup."""
    response = client.get("/simulator/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_running"] is False
    assert data["is_paused"] is False
    assert data["current_scenario"] == "NORMAL"


def test_simulator_scenario_transition():
    """Verify that updating simulator scenarios works and validates the input."""
    # Test valid scenario
    response = client.post("/simulator/scenario", json={"scenario": "REVIEW_BOTTLENECK"})
    assert response.status_code == 200
    assert response.json()["message"] == "Scenario updated to REVIEW_BOTTLENECK"
    assert state.current_scenario == "REVIEW_BOTTLENECK"
    
    # Test invalid scenario
    response = client.post("/simulator/scenario", json={"scenario": "INVALID_SCENARIO"})
    assert response.status_code == 400


def test_simulator_manual_tick():
    """Verify that manual tick generation is deterministic and works."""
    # Reset state to default NORMAL
    client.post("/simulator/scenario", json={"scenario": "NORMAL"})
    
    # Trigger manual tick
    response = client.post("/simulator/tick")
    assert response.status_code == 200
    data = response.json()
    assert "events_count" in data
    assert "events" in data
    
    for event in data["events"]:
        assert event["provider"] == "simulator"
        assert "event_type" in event
        assert "event_timestamp" in event
        assert "payload" in event
        
        # Verify metadata present
        payload = event["payload"]
        assert payload["organization_external_id"] == state.org_id
        assert payload["team_external_id"] == state.team_id
        assert payload["repository_external_id"] == state.repository_id
        assert payload["project_external_id"] == state.project_id
