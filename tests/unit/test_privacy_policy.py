import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.database import SessionLocal
from backend.app.models.core import CanonicalEvent, Organization, Team
from backend.app.models.raw import ProviderEvent
from backend.app.privacy.policy import (
    count_contributors,
    is_small_team,
    mask_evidence,
    mask_identity,
    suppression_metadata,
)


def _seed_team_with_actors(db, actor_refs: list[str]) -> uuid.UUID:
    org = Organization(id=uuid.uuid4(), name=f"Policy Org {uuid.uuid4().hex[:6]}")
    team = Team(
        id=uuid.uuid4(),
        organization_id=org.id,
        name=f"Policy Team {uuid.uuid4().hex[:6]}",
    )
    db.add_all([org, team])
    db.commit()
    now = datetime.now(timezone.utc)
    for i, actor in enumerate(actor_refs):
        raw_event = ProviderEvent(
            provider="policy-test",
            external_event_id=f"policy-evt-{uuid.uuid4().hex[:8]}",
            event_type="CHANGE_CREATED",
            payload={},
            source="policy-test",
        )
        db.add(raw_event)
        db.flush()
        db.add(
            CanonicalEvent(
                id=uuid.uuid4(),
                raw_event_id=raw_event.id,
                organization_id=org.id,
                team_id=team.id,
                event_type="CHANGE_CREATED",
                occurred_at=now - timedelta(minutes=i),
                actor_ref=actor,
                metadata_json={},
            )
        )
    db.commit()
    return team.id


def test_small_team_threshold_and_suppression_metadata():
    assert is_small_team(3) is True
    assert is_small_team(5) is False
    meta = suppression_metadata(3)
    assert meta["suppressed"] is True
    assert meta["min_team_size"] == 5
    assert meta["contributors"] == 3
    assert meta["reason"] == "small_team_aggregation_threshold"


def test_mask_evidence_replaces_values_and_marks_suppressed():
    masked = mask_evidence({"review_time": {"value": 4.2, "normalized": 0.8}})
    assert masked["review_time"]["value"] is None
    assert masked["review_time"]["normalized"] is None
    assert masked["suppressed"] is True


def test_mask_identity_pseudonymises_actor_refs_and_redacts_emails():
    masked = mask_identity(
        {"actor_ref": "dev-3@codesense.io", "note": "ping dev-3@codesense.io"}
    )
    assert masked["actor_ref"].startswith("actor-")
    assert masked["actor_ref"] != "dev-3@codesense.io"
    assert "dev-3@codesense.io" not in masked["note"]
    assert masked["note"] == "***"


def test_count_contributors_counts_distinct_actor_refs():
    db = SessionLocal()
    try:
        team_id = _seed_team_with_actors(db, ["a@x.io", "a@x.io", "b@x.io"])
        assert count_contributors(db, team_id) == 2
    finally:
        db.close()
