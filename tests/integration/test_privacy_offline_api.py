"""Phase 20 privacy — the policy applied at the analytics read boundary.

Covers read-time masking of small-team metric evidence, the fail-closed
organisation scoping rule, and raw-event payload hiding / identity masking.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.core.settings import settings
from backend.app.main import app
from backend.app.models.analytics import (
    Anomaly,
    Bottleneck,
    HealthScore,
    Insight,
    MetricDefinition,
)
from backend.app.models.core import CanonicalEvent, Organization, Team
from backend.app.models.raw import ProviderEvent

client = TestClient(app)

EVIDENCE = {"deployment_frequency": {"value": 3.0}, "review_time": 4.2}


def _component_metrics() -> dict:
    """A fresh copy of the stored component metrics (never a shared constant)."""
    return {
        "delivery": {
            "score": 88.0,
            "weight": 0.25,
            "metrics": {"deployment_frequency": {"value": 3.0}},
        }
    }


def _seed_team(
    db, actor_refs: list[str]
) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    """Create an organisation + team with one canonical event per actor.

    Returns ``(organization_id, team_id, raw_event_ids)``.
    """
    org = Organization(id=uuid.uuid4(), name=f"P Org {uuid.uuid4().hex[:6]}")
    team = Team(
        id=uuid.uuid4(),
        organization_id=org.id,
        name=f"P Team {uuid.uuid4().hex[:6]}",
    )
    db.add_all([org, team])
    db.commit()
    now = datetime.now(timezone.utc)
    raw_ids: list[uuid.UUID] = []
    for index, actor in enumerate(actor_refs):
        raw = ProviderEvent(
            provider="privacy-test",
            external_event_id=f"privacy-evt-{uuid.uuid4().hex[:8]}",
            event_type="CHANGE_CREATED",
            event_timestamp=now,
            payload={},
            source="privacy-test",
        )
        db.add(raw)
        db.flush()
        raw_ids.append(raw.id)
        db.add(
            CanonicalEvent(
                id=uuid.uuid4(),
                raw_event_id=raw.id,
                organization_id=org.id,
                team_id=team.id,
                event_type="CHANGE_CREATED",
                occurred_at=now - timedelta(minutes=index),
                actor_ref=actor,
                metadata_json={},
            )
        )
    db.commit()
    return org.id, team.id, raw_ids


def _seed_detections(db, organization_id, team_id) -> dict[str, uuid.UUID]:
    """Seed one insight, one anomaly and one bottleneck for a team."""
    metric = MetricDefinition(
        id=uuid.uuid4(),
        metric_key=f"metric-{uuid.uuid4().hex[:8]}",
        name="Deployment frequency",
    )
    db.add(metric)
    db.flush()
    insight = Insight(
        id=uuid.uuid4(),
        organization_id=organization_id,
        team_id=team_id,
        insight_type="RISK",
        category="delivery",
        severity="medium",
        title="Slow review",
        content="Reviews take too long.",
        confidence=0.8,
        evidence=dict(EVIDENCE),
        source_metrics={"deployment_frequency": 3.0},
        generated_by="RULE_ENGINE",
        status="ACTIVE",
    )
    anomaly = Anomaly(
        id=uuid.uuid4(),
        organization_id=organization_id,
        team_id=team_id,
        metric_id=metric.id,
        severity="high",
        baseline_value=5.0,
        observed_value=1.0,
        change_percent=-80.0,
        confidence=0.9,
        evidence=dict(EVIDENCE),
        detected_at=datetime.now(timezone.utc),
    )
    bottleneck = Bottleneck(
        id=uuid.uuid4(),
        organization_id=organization_id,
        team_id=team_id,
        category="review",
        severity="medium",
        title="Review queue",
        description="Reviews queue up.",
        evidence=dict(EVIDENCE),
        detected_at=datetime.now(timezone.utc),
    )
    db.add_all([insight, anomaly, bottleneck])
    db.commit()
    return {
        "insight": insight.id,
        "anomaly": anomaly.id,
        "bottleneck": bottleneck.id,
        "metric": metric.id,
    }


def _cleanup(db, organization_id, team_id, raw_ids, metric_id=None) -> None:
    """Delete every row seeded for one test."""
    db.query(HealthScore).filter(HealthScore.team_id == team_id).delete(
        synchronize_session=False
    )
    db.query(Anomaly).filter(Anomaly.team_id == team_id).delete(
        synchronize_session=False
    )
    db.query(Bottleneck).filter(Bottleneck.team_id == team_id).delete(
        synchronize_session=False
    )
    db.query(Insight).filter(Insight.organization_id == organization_id).delete(
        synchronize_session=False
    )
    db.query(CanonicalEvent).filter(
        CanonicalEvent.organization_id == organization_id
    ).delete(synchronize_session=False)
    if raw_ids:
        db.query(ProviderEvent).filter(ProviderEvent.id.in_(raw_ids)).delete(
            synchronize_session=False
        )
    if metric_id is not None:
        db.query(MetricDefinition).filter(MetricDefinition.id == metric_id).delete(
            synchronize_session=False
        )
    db.query(Team).filter(Team.id == team_id).delete(synchronize_session=False)
    db.query(Organization).filter(Organization.id == organization_id).delete(
        synchronize_session=False
    )
    db.commit()


@pytest.fixture()
def seeded_small_team():
    """A team of two contributors with one health score."""
    db = SessionLocal()
    organization_id = team_id = score_id = None
    raw_ids: list[uuid.UUID] = []
    stored_component_metrics: dict = {}
    try:
        organization_id, team_id, raw_ids = _seed_team(db, ["a@x.io", "b@x.io"])
        now = datetime.now(timezone.utc)
        score = HealthScore(
            id=uuid.uuid4(),
            organization_id=organization_id,
            team_id=team_id,
            period_start=now - timedelta(days=1),
            period_end=now,
            score=88.0,
            previous_score=90.0,
            score_change=-2.0,
            component_metrics=_component_metrics(),
        )
        db.add(score)
        db.commit()
        score_id = score.id
        stored_component_metrics = dict(score.component_metrics)
    finally:
        db.close()
    yield {
        "team_id": team_id,
        "organization_id": organization_id,
        "score_id": score_id,
        "component_metrics": stored_component_metrics,
    }
    db = SessionLocal()
    try:
        _cleanup(db, organization_id, team_id, raw_ids)
    finally:
        db.close()


@pytest.fixture()
def seeded_large_org():
    """An organisation with enough contributors to be above the threshold."""
    db = SessionLocal()
    organization_id = team_id = insight_id = None
    raw_ids: list[uuid.UUID] = []
    try:
        organization_id, team_id, raw_ids = _seed_team(
            db, [f"actor-{i}@x.io" for i in range(settings.MIN_TEAM_SIZE)]
        )
        insight = Insight(
            id=uuid.uuid4(),
            organization_id=organization_id,
            team_id=None,
            insight_type="RISK",
            category="delivery",
            severity="low",
            title="Org level insight",
            content="Organisation wide observation.",
            confidence=0.7,
            evidence=dict(EVIDENCE),
            source_metrics={"deployment_frequency": 3.0},
            generated_by="RULE_ENGINE",
            status="ACTIVE",
        )
        db.add(insight)
        db.commit()
        insight_id = insight.id
    finally:
        db.close()
    yield {"organization_id": organization_id, "insight_id": insight_id}
    db = SessionLocal()
    try:
        _cleanup(db, organization_id, team_id, raw_ids)
    finally:
        db.close()


def test_health_score_masks_metric_evidence_for_small_team(seeded_small_team):
    resp = client.get(
        "/api/v1/health-score", params={"team_id": str(seeded_small_team["team_id"])}
    )
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["score"] == 88.0
    metrics = item["component_metrics"]["delivery"]["metrics"]
    assert metrics["deployment_frequency"]["value"] is None
    assert item["component_metrics"]["delivery"]["suppressed"] is True
    assert item["privacy"]["suppressed"] is True
    assert item["privacy"]["reason"] == "small_team_aggregation_threshold"

    detail = client.get(f"/api/v1/health-score/{seeded_small_team['score_id']}")
    assert detail.status_code == 200
    detail_item = detail.json()
    assert detail_item["score"] == 88.0
    assert (
        detail_item["component_metrics"]["delivery"]["metrics"]["deployment_frequency"][
            "value"
        ]
        is None
    )
    assert detail_item["privacy"]["suppressed"] is True


def test_masking_does_not_mutate_stored_row(seeded_small_team):
    client.get(
        "/api/v1/health-score", params={"team_id": str(seeded_small_team["team_id"])}
    )
    db = SessionLocal()
    try:
        row = (
            db.query(HealthScore)
            .filter(HealthScore.id == seeded_small_team["score_id"])
            .first()
        )
        assert row.component_metrics == seeded_small_team["component_metrics"]
        assert (
            row.component_metrics["delivery"]["metrics"]["deployment_frequency"][
                "value"
            ]
            == 3.0
        )
    finally:
        db.close()


def test_raw_events_mask_identity_and_hide_payload_by_default():
    db = SessionLocal()
    event = ProviderEvent(
        id=uuid.uuid4(),
        provider="simulator",
        external_event_id=f"ext-{uuid.uuid4().hex[:8]}",
        event_type="CHANGE_CREATED",
        event_timestamp=datetime.now(timezone.utc),
        payload={"actor_ref": "dev-7@codesense.io", "change_id": "pr-1"},
        payload_hash="h",
        source="simulator",
        processing_status="PENDING",
    )
    db.add(event)
    db.commit()
    event_id = event.id
    db.close()
    try:
        resp = client.get("/api/v1/events", params={"provider": "simulator"})
        assert resp.status_code == 200
        item = next(i for i in resp.json()["items"] if i["id"] == str(event_id))
        assert item["payload"] is None
    finally:
        db = SessionLocal()
        try:
            db.query(ProviderEvent).filter(ProviderEvent.id == event_id).delete()
            db.commit()
        finally:
            db.close()


def test_raw_event_payload_is_identity_masked_when_exposed(monkeypatch):
    """When raw payloads are exposed, actor references are pseudonymised."""
    monkeypatch.setattr(settings, "EXPOSE_RAW_PAYLOADS", True)
    db = SessionLocal()
    event = ProviderEvent(
        id=uuid.uuid4(),
        provider="privacy-exposed",
        external_event_id=f"ext-{uuid.uuid4().hex[:8]}",
        event_type="CHANGE_CREATED",
        event_timestamp=datetime.now(timezone.utc),
        payload={"actor_ref": "dev-7@codesense.io", "change_id": "pr-1"},
        payload_hash="h",
        source="simulator",
        processing_status="PENDING",
    )
    db.add(event)
    db.commit()
    event_id = event.id
    db.close()
    try:
        resp = client.get("/api/v1/events", params={"provider": "privacy-exposed"})
        assert resp.status_code == 200
        item = next(i for i in resp.json()["items"] if i["id"] == str(event_id))
        assert item["payload"]["actor_ref"].startswith("actor-")
        assert item["payload"]["actor_ref"] != "dev-7@codesense.io"
        assert item["payload"]["change_id"] == "pr-1"
    finally:
        db = SessionLocal()
        try:
            db.query(ProviderEvent).filter(ProviderEvent.id == event_id).delete()
            db.commit()
        finally:
            db.close()


def test_detections_mask_evidence_for_small_team(seeded_small_team):
    """Insights, anomalies and bottlenecks hide metric evidence for small teams."""
    db = SessionLocal()
    try:
        ids = _seed_detections(
            db, seeded_small_team["organization_id"], seeded_small_team["team_id"]
        )
    finally:
        db.close()

    cases = [
        ("/api/v1/insights", "/api/v1/insights/{id}", "insight"),
        ("/api/v1/anomalies", "/api/v1/anomalies/{id}", "anomaly"),
        ("/api/v1/bottlenecks", "/api/v1/bottlenecks/{id}", "bottleneck"),
    ]
    params = {"team_id": str(seeded_small_team["team_id"])}
    for list_path, detail_path, key in cases:
        resp = client.get(list_path, params=params)
        assert resp.status_code == 200, list_path
        item = next(i for i in resp.json()["items"] if i["id"] == str(ids[key]))
        assert item["evidence"]["deployment_frequency"]["value"] is None, list_path
        assert item["evidence"]["review_time"] is None, list_path
        assert item["evidence"]["suppressed"] is True, list_path
        assert item["privacy"]["suppressed"] is True, list_path
        assert item["privacy"]["reason"] == "small_team_aggregation_threshold", (
            list_path
        )

        detail = client.get(detail_path.format(id=ids[key]))
        assert detail.status_code == 200, detail_path
        detail_item = detail.json()
        assert detail_item["evidence"]["deployment_frequency"]["value"] is None, (
            detail_path
        )
        assert detail_item["privacy"]["suppressed"] is True, detail_path

    db = SessionLocal()
    try:
        _cleanup(
            db,
            seeded_small_team["organization_id"],
            seeded_small_team["team_id"],
            [],
            metric_id=ids["metric"],
        )
    finally:
        db.close()


def test_org_level_insight_is_scoped_by_organization(seeded_large_org):
    """An org-level row is scoped by organization_id, so it is not masked blindly."""
    resp = client.get(
        "/api/v1/insights",
        params={"organization_id": str(seeded_large_org["organization_id"])},
    )
    assert resp.status_code == 200
    item = next(
        i
        for i in resp.json()["items"]
        if i["id"] == str(seeded_large_org["insight_id"])
    )
    assert item["evidence"]["deployment_frequency"]["value"] == 3.0
    assert item["privacy"]["suppressed"] is False
