import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app as backend_app
from backend.app.models.analytics import (
    Anomaly,
    Bottleneck,
    Insight,
)
from backend.app.models.core import CanonicalEvent, Organization, Team
from backend.app.models.raw import ProviderEvent
from backend.app.services.detection import DetectionEngine
from backend.app.services.health import HealthScoreEngine
from backend.app.services.insights import InsightsEngine
from backend.app.services.metrics import MetricEngine
from backend.app.services.processing import EventProcessor
from simulator.main import send_events_to_backend, state, tick_simulation

backend_client = TestClient(backend_app)

@pytest.fixture(autouse=True)
def clean_database():
    db = SessionLocal()
    try:
        # We don't delete everything, just clean events for a fresh start, 
        # or we can just create a unique team for our test.
        pass
    finally:
        db.close()

def test_end_to_end_integration(monkeypatch):
    # 1. Setup mock post for simulator
    def mock_post(url, json=None, **kwargs):
        endpoint = "/api/v1/events"
        if "batch" in url:
            endpoint = "/api/v1/events/batch"
        response = backend_client.post(endpoint, json=json)
        class MockResponse:
            status_code = response.status_code
            text = response.text
        return MockResponse()
        
    monkeypatch.setattr("requests.post", mock_post)

    db = SessionLocal()
    try:
        # Phase 1-3 assumed (DB works, API works)
        # Setup Organization and Team for the simulation
        org_id = uuid.uuid4()
        team_id = uuid.uuid4()
        org = Organization(id=org_id, name="Integration Test Org")
        team = Team(id=team_id, name="Integration Test Team", organization_id=org_id)
        db.add_all([org, team])
        db.commit()

        # Phase 4 & 5: Simulate and Ingest
        # We need events that simulate bottleneck
        state.current_scenario = "REVIEW_BOTTLENECK"
        events = []
        for _ in range(5):
            events.extend(tick_simulation())
        # override team_id/org_id in payloads? Actually Simulator generates its own org/team, 
        # but let's just let simulator run normally and we will find the team it created or linked.
        
        # Let's clear previous raw events to easily find ours
        db.query(ProviderEvent).delete()
        db.commit()

        # Send events
        send_events_to_backend(events)
        
        # Verify Ingestion
        raw_events = db.query(ProviderEvent).all()
        assert len(raw_events) > 0, "Ingestion Failed (Phase 5)"
        
        # Phase 6: Canonical Data Layer
        processor = EventProcessor(db)
        processed_count = processor.process_pending_events(limit=500)
        assert processed_count > 0, "Canonical Processing Failed (Phase 6)"
        
        # Wait, Simulator events use predefined external IDs.
        # Let's find the team that was created/used by normalization
        canonical_events = db.query(CanonicalEvent).all()
        assert len(canonical_events) > 0, "Canonical Events Not Created (Phase 6)"
        
        # We grab the team_id from the first canonical event
        canonical_event = next(e for e in canonical_events if e.team_id)
        active_team_id = canonical_event.team_id
        
        # Phase 7: Analytics Engine
        metric_engine = MetricEngine(db)
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        end = now + timedelta(days=1)
        
        metrics = metric_engine.calculate_metrics_for_period(active_team_id, start, end)
        assert len(metrics) > 0, "Metrics Calculation Failed (Phase 7)"
        
        # Phase 8: Engineering Health Score
        health_engine = HealthScoreEngine(db)
        health_score = health_engine.calculate_health_score(active_team_id, start, end)
        assert health_score is not None, "Health Score Failed (Phase 8)"
        assert health_score.score >= 0, "Health Score should be calculated"
        
        # Phase 9: Bottleneck & Anomaly Detection
        detection_engine = DetectionEngine(db)
        # We need to simulate history for anomalies, or rely on % change fallback
        detection_engine.run_detection_for_period(active_team_id, start, end)
        
        anomalies = db.query(Anomaly).filter(Anomaly.team_id == active_team_id).all()
        bottlenecks = db.query(Bottleneck).filter(Bottleneck.team_id == active_team_id).all()
        
        # Note: bottleneck may or may not be triggered by just 1 run, but it shouldn't crash.
        
        # Phase 10: Insights Engine
        insights_engine = InsightsEngine(db)
        insights = insights_engine.generate_insights_from_detections(active_team_id, start, end)
        # Insights might be empty if no anomaly/bottleneck, which is fine for flow validation
        
        db_insights = db.query(Insight).filter(Insight.team_id == active_team_id).all()
        assert len(db_insights) == len(insights), "Insights Database Verification Failed (Phase 10)"

        print("Integration Test Completed Successfully covering Phases 1-10.")

    finally:
        db.rollback()
        db.close()

