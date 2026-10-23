"""Unit tests for the Jira provider connector (Phase 21 Task 4).

``responses`` is not installed in this environment, so HTTP tests use
``unittest.mock.patch("requests.Session.request")`` instead of
``@responses.activate`` (see task brief Step 1).
"""

from __future__ import annotations

import base64
import uuid
from unittest.mock import Mock, patch

from backend.app.integrations.jira import (
    JiraConfigurationError,
    JiraConnector,
    JiraError,
)


def _connector(extra_config=None) -> JiraConnector:
    config = {
        "base_url": "https://jira.example.com",
        "email": "user@example.com",
        "api_token": "at_test",
        "webhook_secret": "whsec_test",
    }
    if extra_config:
        config.update(extra_config)
    return JiraConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config=config,
    )


def _make_response(status_code=200, json_data=None, headers=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = json_data if json_data is not None else {}
    response.headers = headers or {}
    return response


# --- auth ---


def test_jira_auth_headers_basic_auth():
    conn = _connector()
    headers = conn.auth_headers()
    expected = base64.b64encode(b"user@example.com:at_test").decode("ascii")
    assert headers == {
        "Authorization": f"Basic {expected}",
        "Accept": "application/json",
    }


def test_jira_auth_headers_bearer_pat():
    conn = _connector(extra_config={"pat": "pat_test", "email": "", "api_token": ""})
    headers = conn.auth_headers()
    assert headers == {
        "Authorization": "Bearer pat_test",
        "Accept": "application/json",
    }


# --- fetch ---


@patch("requests.Session.request")
def test_jira_fetch_events_paginates_and_filters_since(mock_request):
    response = _make_response(
        json_data={
            "startAt": 0,
            "maxResults": 50,
            "total": 100,
            "isLast": False,
            "issues": [
                {
                    "key": "PROJ-1",
                    "id": "10001",
                    "fields": {
                        "status": {"name": "To Do"},
                        "created": "2026-01-01T00:00:00.000Z",
                        "updated": "2026-01-01T00:00:00.000Z",
                    },
                }
            ],
        },
    )
    mock_request.return_value = response

    conn = _connector()
    events, cursor, has_more = conn.fetch_events(since="2026-01-01T00:00:00Z")

    assert len(events) == 1
    assert events[0]["key"] == "PROJ-1"
    assert cursor == "1"
    assert has_more is True

    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert "/rest/api/3/search" in args[1]
    assert kwargs["params"]["jql"] == 'updated >= "2026-01-01T00:00:00Z"'
    assert kwargs["params"]["maxResults"] == 50
    assert kwargs["params"]["startAt"] == 0
    expected = base64.b64encode(b"user@example.com:at_test").decode("ascii")
    assert kwargs["headers"]["Authorization"] == f"Basic {expected}"


@patch("requests.Session.request")
def test_jira_fetch_events_second_page_from_cursor(mock_request):
    response = _make_response(
        json_data={"startAt": 50, "maxResults": 50, "isLast": True, "issues": []}
    )
    mock_request.return_value = response

    conn = _connector()
    conn.fetch_events(cursor="50")

    _, kwargs = mock_request.call_args
    assert kwargs["params"]["startAt"] == 50


@patch("requests.Session.request")
def test_jira_fetch_events_excludes_before_since(mock_request):
    response = _make_response(
        json_data={
            "startAt": 0,
            "maxResults": 50,
            "isLast": True,
            "issues": [
                {
                    "key": "PROJ-1",
                    "id": "10001",
                    "fields": {
                        "status": {"name": "To Do"},
                        "updated": "2026-01-02T00:00:00.000Z",
                    },
                },
                {
                    "key": "PROJ-2",
                    "id": "10002",
                    "fields": {
                        "status": {"name": "To Do"},
                        "updated": "2025-12-31T00:00:00.000Z",
                    },
                },
            ],
        }
    )
    mock_request.return_value = response

    conn = _connector()
    events, cursor, has_more = conn.fetch_events(since="2026-01-01T00:00:00Z")

    assert len(events) == 1
    assert events[0]["key"] == "PROJ-1"
    assert cursor is None
    assert has_more is False


@patch("requests.Session.request")
def test_jira_fetch_events_raises_on_non_2xx(mock_request):
    response = _make_response(status_code=404, text="Not Found")
    mock_request.return_value = response

    conn = _connector()
    try:
        conn.fetch_events()
    except JiraError as exc:
        assert "HTTP 404" in str(exc)
    else:
        raise AssertionError("Expected JiraError on non-2xx response")


def test_jira_fetch_events_requires_base_url():
    conn = JiraConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config={"email": "user@example.com", "api_token": "at_test"},
    )
    try:
        conn.fetch_events()
    except JiraConfigurationError as exc:
        assert "base_url" in str(exc).lower()
    else:
        raise AssertionError("Expected JiraConfigurationError without base_url")


# --- mapping ---


def _issue(key, status_name, updated="2026-01-02T00:00:00.000Z", deployment=None):
    fields = {
        "status": {"name": status_name},
        "created": "2026-01-01T00:00:00.000Z",
        "updated": updated,
    }
    if deployment is not None:
        fields["deployment"] = deployment
    return {"key": key, "id": "10001", "fields": fields}


def test_jira_map_issue_created_to_work_item_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            _issue("PROJ-1", "To Do"),
        ]
    )
    assert len(raw) == 1
    assert raw[0]["provider"] == "jira"
    assert raw[0]["external_event_id"] == "jira:PROJ-1"
    assert raw[0]["event_type"] == "WORK_ITEM_CREATED"
    assert raw[0]["source"] == "poll"


def test_jira_map_in_review_to_review_requested():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            _issue("PROJ-2", "In Review"),
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "REVIEW_REQUESTED"


def test_jira_map_code_review_to_review_requested():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            _issue("PROJ-3", "Code Review"),
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "REVIEW_REQUESTED"


def test_jira_map_done_to_review_completed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            _issue("PROJ-4", "Done"),
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "REVIEW_COMPLETED"


def test_jira_map_resolved_to_review_completed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            _issue("PROJ-5", "Resolved"),
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "REVIEW_COMPLETED"


def test_jira_map_deployment_field_to_deployment_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            _issue("PROJ-6", "To Do", deployment="v1.2.3"),
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "DEPLOYMENT_CREATED"


def test_jira_map_unknown_status_defaults_to_work_item_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            _issue("PROJ-7", "Backlog"),
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "WORK_ITEM_CREATED"


def test_jira_map_missing_key_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": "10001",
                "fields": {"status": {"name": "To Do"}},
            }
        ]
    )
    assert raw == []


# --- webhook ---


def test_jira_webhook_to_raw_events_issue_created():
    conn = _connector()
    payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "PROJ-8",
            "id": "10008",
            "fields": {
                "status": {"name": "To Do"},
                "updated": "2026-01-02T00:00:00.000Z",
            },
        },
    }
    raw = conn.webhook_to_raw_events(payload)
    assert len(raw) == 1
    assert raw[0]["source"] == "webhook"
    assert raw[0]["event_type"] == "WORK_ITEM_CREATED"
    assert raw[0]["external_event_id"] == "jira:PROJ-8"


def test_jira_webhook_to_raw_events_issue_updated_done():
    conn = _connector()
    payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "PROJ-9",
            "id": "10009",
            "fields": {
                "status": {"name": "Done"},
                "updated": "2026-01-03T00:00:00.000Z",
            },
        },
    }
    raw = conn.webhook_to_raw_events(payload)
    assert len(raw) == 1
    assert raw[0]["event_type"] == "REVIEW_COMPLETED"
    assert raw[0]["source"] == "webhook"


def test_jira_webhook_signature_verification():
    conn = _connector()
    body = b'{"webhookEvent":"jira:issue_created"}'
    assert conn.verify_webhook_signature(body, "whsec_test") is True
    assert conn.verify_webhook_signature(body, "wrong-secret") is False
    assert conn.verify_webhook_signature(body, None) is False
