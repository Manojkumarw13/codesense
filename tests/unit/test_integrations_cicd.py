"""Unit tests for the CI/CD provider connector (Phase 21 Task 5).

``responses`` is not installed in this environment, so HTTP tests use
``unittest.mock.patch("requests.Session.request")`` instead of
``@responses.activate`` (see task brief Step 1).
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from unittest.mock import Mock, patch

from backend.app.integrations.cicd import (
    CICDConnector,
    CICDError,
)


def _connector(extra_config=None) -> CICDConnector:
    config = {
        "base_url": "https://ci.example.com/api",
        "token": "cicd_token_test",
        "webhook_secret": "whsec_test",
    }
    if extra_config:
        config.update(extra_config)
    return CICDConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config=config,
    )


def _make_response(status_code=200, json_data=None, headers=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = json_data if json_data is not None else []
    response.headers = headers or {}
    return response


# --- auth ---


def test_cicd_auth_headers():
    conn = _connector()
    headers = conn.auth_headers()
    assert headers == {
        "Authorization": "Bearer cicd_token_test",
        "Accept": "application/json",
    }


def test_cicd_auth_headers_missing_token():
    conn = _connector(extra_config={"token": ""})
    headers = conn.auth_headers()
    assert headers == {
        "Authorization": "Bearer ",
        "Accept": "application/json",
    }


# --- fetch ---


@patch("requests.Session.request")
def test_cicd_fetch_events_paginates_and_filters_since(mock_request):
    response = _make_response(
        json_data=[
            {
                "id": "build-1",
                "type": "build",
                "status": "started",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
        headers={"X-Next-Cursor": "cursor-2"},
    )
    mock_request.return_value = response

    conn = _connector()
    events, cursor, has_more = conn.fetch_events(since="2026-01-01T00:00:00Z")

    assert len(events) == 1
    assert events[0]["id"] == "build-1"
    assert cursor == "cursor-2"
    assert has_more is True

    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert "builds" in args[1] or "events" in args[1]
    assert kwargs["params"]["limit"] == 100
    assert kwargs["headers"]["Authorization"] == "Bearer cicd_token_test"


@patch("requests.Session.request")
def test_cicd_fetch_events_second_page_from_cursor(mock_request):
    response = _make_response(json_data=[], headers={})
    mock_request.return_value = response

    conn = _connector()
    conn.fetch_events(cursor="cursor-3")

    _, kwargs = mock_request.call_args
    assert kwargs["params"]["cursor"] == "cursor-3"


@patch("requests.Session.request")
def test_cicd_fetch_events_excludes_before_since(mock_request):
    response = _make_response(
        json_data=[
            {
                "id": "build-1",
                "type": "build",
                "status": "success",
                "created_at": "2026-01-02T00:00:00Z",
            },
            {
                "id": "build-2",
                "type": "build",
                "status": "success",
                "created_at": "2025-12-31T00:00:00Z",
            },
        ]
    )
    mock_request.return_value = response

    conn = _connector()
    events, cursor, has_more = conn.fetch_events(since="2026-01-01T00:00:00Z")

    assert len(events) == 1
    assert events[0]["id"] == "build-1"
    assert cursor is None
    assert has_more is False


@patch("requests.Session.request")
def test_cicd_fetch_events_raises_on_non_2xx(mock_request):
    response = _make_response(status_code=404, json_data={"message": "Not Found"})
    mock_request.return_value = response

    conn = _connector()
    try:
        conn.fetch_events()
    except CICDError as exc:
        assert "HTTP 404" in str(exc)
    else:
        raise AssertionError("Expected CICDError on non-2xx response")


def test_cicd_fetch_events_returns_empty_when_no_base_url():
    conn = CICDConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config={"token": "cicd_token_test"},
    )
    events, cursor, has_more = conn.fetch_events()
    assert events == []
    assert cursor is None
    assert has_more is False


# --- mapping ---


def test_cicd_map_build_started_to_build_started():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "build-1",
                "type": "build",
                "status": "started",
                "created_at": "2026-01-02T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["provider"] == "cicd"
    assert raw[0]["external_event_id"] == "cicd:build-1"
    assert raw[0]["event_type"] == "BUILD_STARTED"
    assert raw[0]["source"] == "poll"


def test_cicd_map_build_success_to_build_completed_and_succeeded():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "build-2",
                "type": "build",
                "status": "success",
                "created_at": "2026-01-03T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 2
    event_types = {e["event_type"] for e in raw}
    assert "BUILD_COMPLETED" in event_types
    assert "BUILD_SUCCEEDED" in event_types
    for e in raw:
        assert e["provider"] == "cicd"
        assert e["external_event_id"] == "cicd:build-2"


def test_cicd_map_build_failed_to_build_completed_and_failed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "build-3",
                "type": "build",
                "status": "failed",
                "created_at": "2026-01-04T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 2
    event_types = {e["event_type"] for e in raw}
    assert "BUILD_COMPLETED" in event_types
    assert "BUILD_FAILED" in event_types


def test_cicd_map_deployment_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "deploy-1",
                "type": "deployment",
                "status": "created",
                "created_at": "2026-01-05T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "DEPLOYMENT_CREATED"


def test_cicd_map_deployment_succeeded():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "deploy-2",
                "type": "deployment",
                "status": "success",
                "created_at": "2026-01-06T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "DEPLOYMENT_SUCCEEDED"


def test_cicd_map_deployment_failed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "deploy-3",
                "type": "deployment",
                "status": "failed",
                "created_at": "2026-01-07T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "DEPLOYMENT_FAILED"


def test_cicd_map_unknown_event_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "unknown-1",
                "type": "unknown_type",
                "status": "whatever",
                "created_at": "2026-01-08T00:00:00Z",
            }
        ]
    )
    assert raw == []


def test_cicd_map_missing_id_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "type": "build",
                "status": "started",
                "created_at": "2026-01-09T00:00:00Z",
            }
        ]
    )
    assert raw == []


# --- webhook ---


def test_cicd_webhook_to_raw_events_build_started():
    conn = _connector()
    payload = {
        "event": "build_started",
        "id": "build-4",
        "type": "build",
        "status": "started",
        "created_at": "2026-01-10T00:00:00Z",
    }
    raw = conn.webhook_to_raw_events(payload)
    assert len(raw) == 1
    assert raw[0]["source"] == "webhook"
    assert raw[0]["event_type"] == "BUILD_STARTED"
    assert raw[0]["external_event_id"] == "cicd:build-4"


def test_cicd_webhook_to_raw_events_deployment_failed():
    conn = _connector()
    payload = {
        "event": "deployment_failed",
        "id": "deploy-4",
        "type": "deployment",
        "status": "failed",
        "created_at": "2026-01-11T00:00:00Z",
    }
    raw = conn.webhook_to_raw_events(payload)
    assert len(raw) == 1
    assert raw[0]["event_type"] == "DEPLOYMENT_FAILED"
    assert raw[0]["source"] == "webhook"


def test_cicd_webhook_signature_verification():
    conn = _connector()
    body = b'{"event":"build_started","id":"build-5"}'
    sig = "sha256=" + hmac.new(b"whsec_test", body, hashlib.sha256).hexdigest()
    assert conn.verify_webhook_signature(body, sig) is True
    assert conn.verify_webhook_signature(body, "sha256=wrong") is False
    assert conn.verify_webhook_signature(body, None) is False


def test_cicd_webhook_signature_missing_secret():
    conn = _connector(extra_config={"webhook_secret": ""})
    body = b'{"event":"build_started"}'
    assert conn.verify_webhook_signature(body, "sha256=anysig") is False
    assert conn.verify_webhook_signature(body, "") is False
    assert conn.verify_webhook_signature(body, None) is False
