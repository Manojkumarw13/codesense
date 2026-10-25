import uuid
from datetime import datetime, timedelta, timezone

from backend.app.core.database import SessionLocal
from backend.app.models.core import CanonicalEvent, Organization, Team
from backend.app.models.raw import ProviderEvent
from backend.app.privacy.gateway import PrivacyBlockedError, PrivacyGateway
from backend.app.privacy.policy import (
    count_contributors,
    count_contributors_by_scope,
    is_small_team,
    mask_evidence,
    mask_identity,
    suppression_metadata,
)


def _seed_event(db, team_id, org_id, actor_ref, occurred_at):
    raw = ProviderEvent(
        provider="priv",
        external_event_id=f"priv-{uuid.uuid4().hex[:8]}",
        event_type="CHANGE_CREATED",
        payload={},
        source="priv",
    )
    db.add(raw)
    db.flush()
    db.add(
        CanonicalEvent(
            id=uuid.uuid4(),
            raw_event_id=raw.id,
            organization_id=org_id,
            team_id=team_id,
            event_type="CHANGE_CREATED",
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            metadata_json={},
        )
    )


def test_gateway_sanitizes_clean_aggregate_context_and_strips_raw_keys():
    ctx = {
        "team_id": str(uuid.uuid4()),
        "score": 85.0,
        "dimensions": {"delivery": 90.0},
        "payload": {"secret": "raw blob"},
        "raw_payload": {"more": "raw"},
    }
    safe = PrivacyGateway().sanitize(ctx)
    assert safe["score"] == 85.0
    assert safe["dimensions"]["delivery"] == 90.0
    assert "payload" not in safe
    assert "raw_payload" not in safe


def test_gateway_blocks_identity_keys():
    for key in ("actor_ref", "developer", "author", "assignee", "email", "user_id"):
        ctx = {"team_id": str(uuid.uuid4()), key: "dev-1@codesense.io"}
        try:
            PrivacyGateway().sanitize(ctx)
        except PrivacyBlockedError:
            continue
        else:
            raise AssertionError(f"expected PrivacyBlockedError for key {key!r}")


def test_gateway_blocks_email_in_free_text():
    ctx = {"team_id": str(uuid.uuid4()), "note": "ping dev-1@codesense.io please"}
    try:
        PrivacyGateway().sanitize(ctx)
    except PrivacyBlockedError:
        pass
    else:
        raise AssertionError("expected PrivacyBlockedError for email in free text")


def test_gateway_blocks_nested_identity():
    ctx = {"team_id": str(uuid.uuid4()), "metrics": {"reviewer": "sam@codesense.io"}}
    try:
        PrivacyGateway().sanitize(ctx)
    except PrivacyBlockedError:
        pass
    else:
        raise AssertionError("expected PrivacyBlockedError for nested identity")


def test_gateway_rejects_non_dict_context():
    try:
        PrivacyGateway().sanitize(["not", "a", "dict"])
    except PrivacyBlockedError:
        pass
    else:
        raise AssertionError("expected PrivacyBlockedError for non-dict context")


def test_small_team_boundary():
    assert is_small_team(4) is True
    assert is_small_team(5) is False
    assert is_small_team(0) is True


def test_suppression_metadata_shape():
    meta = suppression_metadata(3)
    assert meta == {
        "suppressed": True,
        "min_team_size": 5,
        "contributors": 3,
        "reason": "small_team_aggregation_threshold",
    }


def test_mask_evidence_none_returns_suppression_marker():
    assert mask_evidence(None) == {
        "suppressed": True,
        "reason": "small_team_aggregation_threshold",
    }


def test_count_contributors_by_scope_multiple_scopes():
    db = SessionLocal()
    try:
        org_id = uuid.uuid4()
        team_id = uuid.uuid4()
        org = Organization(id=org_id, name="Scope Org")
        team = Team(id=team_id, organization_id=org_id, name="Scope Team")
        db.add_all([org, team])
        db.commit()
        now = datetime.now(timezone.utc)
        _seed_event(db, team_id, org_id, "a@x.io", now - timedelta(days=1))
        _seed_event(db, team_id, org_id, "b@x.io", now - timedelta(days=2))
        db.commit()

        s1 = (team_id, org_id, now - timedelta(days=7), now)
        s2 = (team_id, None, None, None)
        counts = count_contributors_by_scope(db, [s1, s2])
        assert counts[s1] == 2
        assert counts[s2] == 2
    finally:
        db.rollback()
        db.close()


def test_count_contributors_window_and_null():
    db = SessionLocal()
    try:
        org_id = uuid.uuid4()
        team_id = uuid.uuid4()
        org = Organization(id=org_id, name="W Org")
        team = Team(id=team_id, organization_id=org_id, name="W Team")
        db.add_all([org, team])
        db.commit()
        now = datetime.now(timezone.utc)
        _seed_event(db, team_id, org_id, "in@x.io", now - timedelta(days=1))
        _seed_event(db, team_id, org_id, "out@x.io", now - timedelta(days=30))
        _seed_event(db, team_id, org_id, None, now)
        db.commit()

        assert count_contributors(db, team_id) == 2
        assert count_contributors(db, team_id, since=now - timedelta(days=7)) == 1
    finally:
        db.rollback()
        db.close()


def test_mask_identity_plural_actor_keys_stable_per_element():
    masked = mask_identity({"reviewers": ["dev-1@x.io", "dev-2@x.io"]})
    assert masked["reviewers"][0].startswith("actor-")
    assert masked["reviewers"][1].startswith("actor-")
    assert masked["reviewers"][0] != masked["reviewers"][1]
    again = mask_identity({"reviewers": ["dev-1@x.io", "dev-2@x.io"]})
    assert again == masked
