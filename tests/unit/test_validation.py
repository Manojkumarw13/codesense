import uuid

import pytest
from pydantic import ValidationError

from backend.app.schemas.event import ProviderEventCreate


def _valid_event(**overrides):
    data = {
        "provider": "github",
        "external_event_id": f"evt-{uuid.uuid4().hex[:8]}",
        "event_type": "CHANGE_CREATED",
        "payload": {"number": 42},
        "source": "webhook",
    }
    data.update(overrides)
    return data


def test_valid_event_accepted_and_stripped():
    event = ProviderEventCreate(
        **_valid_event(provider="  GitHub  ", source="  webhook  ")
    )
    assert event.provider == "GitHub"
    assert event.source == "webhook"
    assert isinstance(event.payload, dict)


def test_empty_fields_rejected():
    for field in ("provider", "external_event_id", "event_type", "source"):
        with pytest.raises(ValidationError):
            ProviderEventCreate(**_valid_event(**{field: ""}))


def test_whitespace_only_fields_rejected():
    for field in ("provider", "external_event_id", "event_type", "source"):
        with pytest.raises(ValidationError):
            ProviderEventCreate(**_valid_event(**{field: "   \t\n  "}))


def test_payload_must_be_dict():
    with pytest.raises(ValidationError):
        ProviderEventCreate(**_valid_event(payload="not-a-dict"))


def test_event_timestamp_optional():
    event = ProviderEventCreate(**_valid_event(event_timestamp=None))
    assert event.event_timestamp is None


def test_external_event_id_is_required():
    with pytest.raises(ValidationError):
        ProviderEventCreate(
            provider="github",
            event_type="CHANGE_CREATED",
            payload={},
            source="webhook",
        )
