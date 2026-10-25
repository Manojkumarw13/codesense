"""Phase 20 privacy — the policy applied at the analytics read boundary.

Covers read-time masking of small-team metric evidence, the fail-closed
organisation scoping rule, and raw-event payload hiding / identity masking.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from backend.app.core.database import SessionLocal, engine
from backend.app.core.settings import settings
from backend.app.main import app
from backend.app.auth.auth import create_access_token, hash_password
from backend.app.models.analytics import (
    Anomaly,
    Bottleneck,
    HealthScore,
    Insight,
    MetricDefinition,
)
from backend.app.models.core import (
    CanonicalEvent,
    Organization,
    Role,
    Team,
    TeamMember,
    User,
    UserRole,
)
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


def _recent_events(actor_refs: list[str]) -> list[tuple[str, datetime]]:
    """One event per actor, one minute apart, ending now."""
    now = datetime.now(timezone.utc)
    return [
        (actor, now - timedelta(minutes=index))
        for index, actor in enumerate(actor_refs)
    ]


def _seed_team(
    db, events: list[tuple[str | None, datetime]]
) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    """Create an organisation + team with the given canonical events.

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
    raw_ids: list[uuid.UUID] = []
    for actor, occurred_at in events:
        raw = ProviderEvent(
            provider="privacy-test",
            external_event_id=f"privacy-evt-{uuid.uuid4().hex[:8]}",
            event_type="CHANGE_CREATED",
            event_timestamp=occurred_at,
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
                occurred_at=occurred_at,
                actor_ref=actor,
                metadata_json={},
            )
        )
    db.commit()
    return org.id, team.id, raw_ids


def _seed_detections(db, organization_id, team_id) -> dict[str, uuid.UUID]:
    """Seed one insight, one anomaly and one bottleneck for a team."""
    now = datetime.now(timezone.utc)
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
        created_at=now,
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
        detected_at=now,
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
        detected_at=now,
    )
    db.add_all([insight, anomaly, bottleneck])
    db.commit()
    return {
        "insight": insight.id,
        "anomaly": anomaly.id,
        "bottleneck": bottleneck.id,
        "metric": metric.id,
    }


def _seed_authenticated_member(
    db, organization_id: uuid.UUID, team_id: uuid.UUID, role_name: str = "DEVELOPER"
) -> str:
    """Seed an active team member with ``role_name`` and return a bearer token.

    Used by Phase 20 privacy tests whose callers must now satisfy the
    authentication + team guards on the analytics read endpoints. The test's
    own assertions (masking / scoping) are unchanged; only the session gains a
    valid credential.
    """
    role = Role(id=uuid.uuid4(), name=role_name)
    user = User(
        id=uuid.uuid4(),
        organization_id=organization_id,
        email=f"member-{uuid.uuid4().hex[:8]}@x.io",
        password_hash=hash_password("Password1!"),
        status="ACTIVE",
    )
    db.add_all([role, user])
    db.commit()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.add(TeamMember(team_id=team_id, user_id=user.id))
    db.commit()
    return create_access_token({"sub": str(user.id)})


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
        organization_id, team_id, raw_ids = _seed_team(
            db, _recent_events(["a@x.io", "b@x.io"])
        )
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
        access_token = _seed_authenticated_member(db, organization_id, team_id)
    finally:
        db.close()
    yield {
        "team_id": team_id,
        "organization_id": organization_id,
        "score_id": score_id,
        "component_metrics": stored_component_metrics,
        "access_token": access_token,
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
            db,
            _recent_events([f"actor-{i}@x.io" for i in range(settings.MIN_TEAM_SIZE)]),
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
        access_token = _seed_authenticated_member(db, organization_id, team_id)
    finally:
        db.close()
    yield {
        "organization_id": organization_id,
        "insight_id": insight_id,
        "access_token": access_token,
    }
    db = SessionLocal()
    try:
        _cleanup(db, organization_id, team_id, raw_ids)
    finally:
        db.close()


@pytest.fixture()
def seeded_detections(seeded_small_team):
    """One insight, one anomaly and one bottleneck for the small team."""
    db = SessionLocal()
    try:
        ids = _seed_detections(
            db, seeded_small_team["organization_id"], seeded_small_team["team_id"]
        )
    finally:
        db.close()
    yield ids
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


@pytest.fixture()
def seeded_team_with_one_active_contributor():
    """A team with many lifetime contributors but one inside the scored period."""
    db = SessionLocal()
    organization_id = team_id = score_id = None
    raw_ids: list[uuid.UUID] = []
    try:
        now = datetime.now(timezone.utc)
        events = [
            (f"lapsed-{index}@x.io", now - timedelta(days=30))
            for index in range(settings.MIN_TEAM_SIZE)
        ]
        events.append(("active@x.io", now - timedelta(hours=1)))
        organization_id, team_id, raw_ids = _seed_team(db, events)
        score = HealthScore(
            id=uuid.uuid4(),
            organization_id=organization_id,
            team_id=team_id,
            period_start=now - timedelta(days=1),
            period_end=now,
            score=70.0,
            previous_score=72.0,
            score_change=-2.0,
            component_metrics=_component_metrics(),
        )
        db.add(score)
        db.commit()
        score_id = score.id
        access_token = _seed_authenticated_member(db, organization_id, team_id)
    finally:
        db.close()
    yield {"team_id": team_id, "score_id": score_id, "access_token": access_token}
    db = SessionLocal()
    try:
        _cleanup(db, organization_id, team_id, raw_ids)
    finally:
        db.close()


@pytest.fixture()
def seeded_team_with_one_recent_contributor():
    """A team with many lifetime contributors but one inside the window.

    The lapsed contributors are older than
    ``settings.PRIVACY_DETECTION_WINDOW_DAYS``, so only the recent one is
    inside the trailing window that ends at a detection's timestamp.
    """
    db = SessionLocal()
    organization_id = team_id = None
    raw_ids: list[uuid.UUID] = []
    ids: dict[str, uuid.UUID] = {}
    try:
        now = datetime.now(timezone.utc)
        events = [
            (f"lapsed-{index}@x.io", now - timedelta(days=45))
            for index in range(settings.MIN_TEAM_SIZE)
        ]
        events.append(("recent@x.io", now - timedelta(hours=1)))
        organization_id, team_id, raw_ids = _seed_team(db, events)
        ids = _seed_detections(db, organization_id, team_id)
        access_token = _seed_authenticated_member(db, organization_id, team_id)
    finally:
        db.close()
    yield {
        "team_id": team_id,
        "organization_id": organization_id,
        **ids,
        "access_token": access_token,
    }
    db = SessionLocal()
    try:
        _cleanup(
            db,
            organization_id,
            team_id,
            raw_ids,
            metric_id=ids["metric"],
        )
    finally:
        db.close()


@pytest.fixture()
def counted_queries():
    """Capture every SQL statement the request path issues."""
    statements: list[str] = []

    def _record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _record)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", _record)


def test_health_score_masks_metric_evidence_for_small_team(seeded_small_team):
    resp = client.get(
        "/api/v1/health-score",
        params={"team_id": str(seeded_small_team["team_id"])},
        headers={"Authorization": f"Bearer {seeded_small_team['access_token']}"},
    )
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["score"] == 88.0
    metrics = item["component_metrics"]["delivery"]["metrics"]
    assert metrics["deployment_frequency"]["value"] is None
    assert item["component_metrics"]["delivery"]["suppressed"] is True
    assert item["privacy"]["suppressed"] is True
    assert item["privacy"]["reason"] == "small_team_aggregation_threshold"

    detail = client.get(
        f"/api/v1/health-score/{seeded_small_team['score_id']}",
        headers={"Authorization": f"Bearer {seeded_small_team['access_token']}"},
    )
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
        "/api/v1/health-score",
        params={"team_id": str(seeded_small_team["team_id"])},
        headers={"Authorization": f"Bearer {seeded_small_team['access_token']}"},
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


def test_raw_events_mask_identity_and_hide_payload_by_default(monkeypatch):
    """Raw payloads stay hidden unless the deployment opts in."""
    monkeypatch.setattr(settings, "EXPOSE_RAW_PAYLOADS", False)
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


def test_detections_mask_evidence_for_small_team(seeded_small_team, seeded_detections):
    """Insights, anomalies and bottlenecks hide metric evidence for small teams."""
    ids = seeded_detections
    cases = [
        ("/api/v1/insights", "/api/v1/insights/{id}", "insight"),
        ("/api/v1/anomalies", "/api/v1/anomalies/{id}", "anomaly"),
        ("/api/v1/bottlenecks", "/api/v1/bottlenecks/{id}", "bottleneck"),
    ]
    params = {"team_id": str(seeded_small_team["team_id"])}
    headers = {"Authorization": f"Bearer {seeded_small_team['access_token']}"}
    for list_path, detail_path, key in cases:
        resp = client.get(
            list_path,
            params=params,
            headers=headers,
        )
        assert resp.status_code == 200, list_path
        item = next(i for i in resp.json()["items"] if i["id"] == str(ids[key]))
        assert item["evidence"]["deployment_frequency"]["value"] is None, list_path
        assert item["evidence"]["review_time"] is None, list_path
        assert item["evidence"]["suppressed"] is True, list_path
        assert item["privacy"]["suppressed"] is True, list_path
        assert item["privacy"]["reason"] == "small_team_aggregation_threshold", (
            list_path
        )

        detail = client.get(
            detail_path.format(id=ids[key]),
            headers=headers,
        )
        assert detail.status_code == 200, detail_path
        detail_item = detail.json()
        assert detail_item["evidence"]["deployment_frequency"]["value"] is None, (
            detail_path
        )
        assert detail_item["privacy"]["suppressed"] is True, detail_path


def test_detection_responses_keep_dashboard_fields(
    seeded_small_team, seeded_detections
):
    """The shipped dashboard reads source_metrics and metric_id - keep them."""
    ids = seeded_detections
    params = {"team_id": str(seeded_small_team["team_id"])}
    headers = {"Authorization": f"Bearer {seeded_small_team['access_token']}"}

    resp = client.get("/api/v1/insights", params=params, headers=headers)
    assert resp.status_code == 200
    insight = next(i for i in resp.json()["items"] if i["id"] == str(ids["insight"]))
    assert "source_metrics" in insight
    assert insight["source_metrics"] == {"deployment_frequency": 3.0}
    for key in ("id", "severity", "confidence", "evidence", "privacy"):
        assert key in insight, key

    resp = client.get("/api/v1/anomalies", params=params, headers=headers)
    assert resp.status_code == 200
    anomaly = next(i for i in resp.json()["items"] if i["id"] == str(ids["anomaly"]))
    assert "metric_id" in anomaly
    assert anomaly["metric_id"] == str(ids["metric"])
    for key in ("id", "severity", "confidence", "evidence", "privacy"):
        assert key in anomaly, key


def test_health_score_masks_when_only_one_contributor_in_period(
    seeded_team_with_one_active_contributor,
):
    """Many lifetime contributors but one in the period -> still masked.

    The effective count is ``min(period count, all-time count)``, so a team
    that was busy once cannot expose a single person's behaviour through a
    period that only one contributor was active in.
    """
    if settings.MIN_TEAM_SIZE < 2:
        pytest.skip("the aggregation threshold cannot distinguish one contributor")
    resp = client.get(
        "/api/v1/health-score",
        params={"team_id": str(seeded_team_with_one_active_contributor["team_id"])},
        headers={
            "Authorization": f"Bearer {seeded_team_with_one_active_contributor['access_token']}"
        },
    )
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["privacy"]["suppressed"] is True
    assert item["privacy"]["contributors"] == 1
    metrics = item["component_metrics"]["delivery"]["metrics"]
    assert metrics["deployment_frequency"]["value"] is None


def test_detections_mask_when_only_one_contributor_in_window(
    seeded_team_with_one_recent_contributor,
):
    """Many lifetime contributors but one in the window -> still masked.

    A detection describes the period it was raised in. When only one person
    was active in that window the evidence describes one person and must
    not be readable, however many contributors the team had in total.
    """
    seeded = seeded_team_with_one_recent_contributor
    params = {"team_id": str(seeded["team_id"])}
    headers = {"Authorization": f"Bearer {seeded['access_token']}"}
    cases = [
        ("/api/v1/insights", "insight"),
        ("/api/v1/anomalies", "anomaly"),
        ("/api/v1/bottlenecks", "bottleneck"),
    ]
    for path, key in cases:
        resp = client.get(path, params=params, headers=headers)
        assert resp.status_code == 200, path
        item = next(i for i in resp.json()["items"] if i["id"] == str(seeded[key]))
        assert item["evidence"]["deployment_frequency"]["value"] is None, path
        assert item["privacy"]["suppressed"] is True, path
        assert item["privacy"]["contributors"] == 1, path


def test_contributor_count_is_queried_once_per_scope(
    seeded_small_team, counted_queries
):
    """A page of rows for one team costs one contributor count, not one per row."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        for index in range(10):
            db.add(
                Insight(
                    id=uuid.uuid4(),
                    organization_id=seeded_small_team["organization_id"],
                    team_id=seeded_small_team["team_id"],
                    insight_type="RISK",
                    category="delivery",
                    severity="low",
                    title=f"Insight {index}",
                    content="Body.",
                    confidence=0.5,
                    evidence=dict(EVIDENCE),
                    source_metrics={},
                    generated_by="RULE_ENGINE",
                    status="ACTIVE",
                    # A distinct timestamp per row -> a distinct detection
                    # window per row; the count must still cost one query.
                    created_at=now - timedelta(minutes=index),
                )
            )
        db.commit()
    finally:
        db.close()

    counted_queries.clear()
    resp = client.get(
        "/api/v1/insights",
        params={"team_id": str(seeded_small_team["team_id"])},
        headers={"Authorization": f"Bearer {seeded_small_team['access_token']}"},
    )
    assert resp.status_code == 200
    count_queries = [s for s in counted_queries if "canonical_events" in s]
    assert len(count_queries) == 1, count_queries

    # The health score needs two scopes (the score period and the team
    # history); they still cost a single statement.
    counted_queries.clear()
    resp = client.get(
        "/api/v1/health-score",
        params={"team_id": str(seeded_small_team["team_id"])},
        headers={"Authorization": f"Bearer {seeded_small_team['access_token']}"},
    )
    assert resp.status_code == 200
    count_queries = [s for s in counted_queries if "canonical_events" in s]
    assert len(count_queries) == 1, count_queries


def test_org_level_insight_is_scoped_by_organization(seeded_large_org):
    """An org-level row is scoped by organization_id, so it is not masked blindly."""
    resp = client.get(
        "/api/v1/insights",
        params={"organization_id": str(seeded_large_org["organization_id"])},
        headers={"Authorization": f"Bearer {seeded_large_org['access_token']}"},
    )
    assert resp.status_code == 200
    item = next(
        i
        for i in resp.json()["items"]
        if i["id"] == str(seeded_large_org["insight_id"])
    )
    assert item["evidence"]["deployment_frequency"]["value"] == 3.0
    assert item["privacy"]["suppressed"] is False
