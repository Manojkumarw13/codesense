import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.api.endpoints.events import compute_payload_hash
from backend.app.core.database import SessionLocal
from backend.app.models.raw import ProviderEvent


def _event_row(
    db, provider="github", external_event_id=None, payload=None, **overrides
):
    row = ProviderEvent(
        provider=provider,
        external_event_id=external_event_id or f"evt-{uuid.uuid4().hex[:8]}",
        event_type="CHANGE_CREATED",
        payload=payload or {"number": 1},
        source="webhook",
        processing_status="PENDING",
    )
    row.__dict__.update(overrides)
    db.add(row)
    db.flush()
    return row


def test_payload_hash_is_deterministic():
    payload = {"number": 42, "action": "opened"}
    assert compute_payload_hash(payload) == compute_payload_hash(payload)


def test_payload_hash_ignores_key_order():
    assert compute_payload_hash({"a": 1, "b": 2}) == compute_payload_hash(
        {"b": 2, "a": 1}
    )


def test_payload_hash_changes_with_payload():
    assert compute_payload_hash({"number": 1}) != compute_payload_hash({"number": 2})


def test_dedup_query_finds_existing_event():
    db = SessionLocal()
    try:
        row = _event_row(db)
        existing = (
            db.query(ProviderEvent)
            .filter_by(provider=row.provider, external_event_id=row.external_event_id)
            .first()
        )
        assert existing is not None
        assert existing.id == row.id
    finally:
        db.rollback()
        db.close()


def test_dedup_query_distinguishes_provider():
    db = SessionLocal()
    try:
        ext = f"shared-{uuid.uuid4().hex[:8]}"
        _event_row(db, provider="github", external_event_id=ext)
        # Same external id, different provider -> not a duplicate for github query
        existing = (
            db.query(ProviderEvent)
            .filter_by(provider="gitlab", external_event_id=ext)
            .first()
        )
        assert existing is None
    finally:
        db.rollback()
        db.close()


def test_dedup_query_distinguishes_external_id():
    db = SessionLocal()
    try:
        _event_row(db, provider="github", external_event_id="evt-a")
        existing = (
            db.query(ProviderEvent)
            .filter_by(provider="github", external_event_id="evt-b")
            .first()
        )
        assert existing is None
    finally:
        db.rollback()
        db.close()


def test_db_unique_constraint_rejects_true_duplicate():
    db = SessionLocal()
    try:
        ext = f"dup-{uuid.uuid4().hex[:8]}"
        _event_row(db, provider="github", external_event_id=ext)
        db.commit()
        # Second insert with same provider + external_event_id must violate the constraint.
        dup = ProviderEvent(
            provider="github",
            external_event_id=ext,
            event_type="CHANGE_CREATED",
            payload={"number": 2},
            source="webhook",
            processing_status="PENDING",
        )
        db.add(dup)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.rollback()
        db.close()
