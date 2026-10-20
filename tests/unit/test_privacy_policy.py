import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.database import SessionLocal
from backend.app.core.settings import settings
from backend.app.models.core import CanonicalEvent, Organization, Team
from backend.app.models.raw import ProviderEvent
from backend.app.privacy.policy import (
    count_contributors,
    is_small_team,
    mask_evidence,
    mask_identity,
    suppression_metadata,
)


def _seed_team(
    db,
    events: list[tuple[str | None, datetime]],
) -> tuple[uuid.UUID, uuid.UUID]:
    """Seed one team plus canonical events. Returns (team_id, organization_id)."""
    org = Organization(id=uuid.uuid4(), name=f"Policy Org {uuid.uuid4().hex[:6]}")
    team = Team(
        id=uuid.uuid4(),
        organization_id=org.id,
        name=f"Policy Team {uuid.uuid4().hex[:6]}",
    )
    db.add_all([org, team])
    db.commit()
    for actor_ref, occurred_at in events:
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
                occurred_at=occurred_at,
                actor_ref=actor_ref,
                metadata_json={},
            )
        )
    db.commit()
    return team.id, org.id


def _seed_team_with_actors(db, actor_refs: list[str]) -> uuid.UUID:
    """Seed one team with one event per actor (newest first)."""
    now = datetime.now(timezone.utc)
    team_id, _ = _seed_team(
        db,
        [(actor, now - timedelta(minutes=i)) for i, actor in enumerate(actor_refs)],
    )
    return team_id


def _cleanup(db, team_id: uuid.UUID) -> None:
    """Delete the rows seeded for one test."""
    team = db.query(Team).filter(Team.id == team_id).first()
    organization_id = team.organization_id if team is not None else None
    raw_ids = [
        row[0]
        for row in db.query(CanonicalEvent.raw_event_id)
        .filter(CanonicalEvent.team_id == team_id)
        .all()
    ]
    db.query(CanonicalEvent).filter(CanonicalEvent.team_id == team_id).delete(
        synchronize_session=False
    )
    if raw_ids:
        db.query(ProviderEvent).filter(ProviderEvent.id.in_(raw_ids)).delete(
            synchronize_session=False
        )
    db.query(Team).filter(Team.id == team_id).delete(synchronize_session=False)
    if organization_id is not None:
        db.query(Organization).filter(Organization.id == organization_id).delete(
            synchronize_session=False
        )
    db.commit()


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
    team_id = None
    try:
        team_id = _seed_team_with_actors(db, ["a@x.io", "a@x.io", "b@x.io"])
        assert count_contributors(db, team_id) == 2
    finally:
        if team_id is not None:
            _cleanup(db, team_id)
        db.close()


def test_mask_identity_is_key_aware():
    """Actor keys are pseudonymised, email keys and free text are redacted."""
    masked = mask_identity(
        {
            "actor_ref": "dev-3@codesense.io",
            "author_email": "jane@corp.com",
            "committer": "sam@corp.com",
            "note": "ping dev-3@codesense.io",
        }
    )
    assert masked["actor_ref"].startswith("actor-")
    assert masked["author_email"] == "***"
    assert masked["committer"].startswith("actor-")
    assert masked["note"] == "***"


def test_pseudonym_is_stable_per_actor():
    """The same actor keeps the same pseudonym; different actors differ."""
    first = mask_identity({"actor_ref": "dev-3@codesense.io"})["actor_ref"]
    second = mask_identity({"actor_ref": "dev-3@codesense.io"})["actor_ref"]
    other = mask_identity({"actor_ref": "dev-9@codesense.io"})["actor_ref"]
    assert first.startswith("actor-")
    assert first == second
    assert first != other


def test_pseudonym_depends_on_salt(monkeypatch):
    """A different salt yields a different pseudonym for the same actor."""
    baseline = mask_identity({"actor_ref": "dev-3@codesense.io"})["actor_ref"]
    monkeypatch.setattr(settings, "PRIVACY_PSEUDONYM_SALT", "a-different-salt")
    salted = mask_identity({"actor_ref": "dev-3@codesense.io"})["actor_ref"]
    assert salted.startswith("actor-")
    assert salted != baseline


def test_count_contributors_respects_window():
    """Events outside the since/until window are not counted."""
    db = SessionLocal()
    team_id = None
    now = datetime.now(timezone.utc)
    try:
        team_id, _ = _seed_team(
            db,
            [
                ("in-window-1@x.io", now - timedelta(days=1)),
                ("in-window-2@x.io", now - timedelta(days=2)),
                ("out-of-window@x.io", now - timedelta(days=30)),
            ],
        )
        assert count_contributors(db, team_id) == 3
        assert count_contributors(db, team_id, since=now - timedelta(days=7)) == 2
        assert count_contributors(db, team_id, until=now - timedelta(days=7)) == 1
    finally:
        if team_id is not None:
            _cleanup(db, team_id)
        db.close()


def test_count_contributors_ignores_null_actor_ref():
    """Canonical events without an actor_ref do not count as contributors."""
    db = SessionLocal()
    team_id = None
    now = datetime.now(timezone.utc)
    try:
        team_id, _ = _seed_team(db, [("a@x.io", now), (None, now)])
        assert count_contributors(db, team_id) == 1
    finally:
        if team_id is not None:
            _cleanup(db, team_id)
        db.close()


def test_count_contributors_without_scope_fails_closed():
    """An unscoped call returns 0 instead of a global, cross-tenant count."""
    db = SessionLocal()
    team_id = None
    now = datetime.now(timezone.utc)
    try:
        team_id, _ = _seed_team(db, [("a@x.io", now), ("b@x.io", now)])
        assert count_contributors(db, team_id) == 2
        assert count_contributors(db, None) == 0
    finally:
        if team_id is not None:
            _cleanup(db, team_id)
        db.close()


def test_count_contributors_scopes_to_organization():
    """An organisation scope counts that organisation's events only."""
    db = SessionLocal()
    team_id = None
    now = datetime.now(timezone.utc)
    try:
        team_id, organization_id = _seed_team(db, [("a@x.io", now), ("b@x.io", now)])
        assert count_contributors(db, None, organization_id=organization_id) == 2
        assert count_contributors(db, team_id, organization_id=organization_id) == 2
    finally:
        if team_id is not None:
            _cleanup(db, team_id)
        db.close()
