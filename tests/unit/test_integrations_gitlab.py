"""Unit tests for the GitLab provider connector (Phase 21 Task 3).

``responses`` is not installed in this environment, so HTTP tests use
``unittest.mock.patch("requests.Session.request")`` instead of
``@responses.activate`` (see task brief Step 1).
"""

from __future__ import annotations

import uuid
from unittest.mock import Mock, patch

from backend.app.integrations.gitlab import (
    GitLabConfigurationError,
    GitLabConnector,
    GitLabError,
)


def _connector(extra_config=None) -> GitLabConnector:
    config = {
        "token": "glpat_test",
        "webhook_secret": "whsec_test",
        "project_id": "12345",
    }
    if extra_config:
        config.update(extra_config)
    return GitLabConnector(
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


def test_gitlab_auth_headers():
    conn = _connector()
    headers = conn.auth_headers()
    assert headers == {"Private-Token": "glpat_test"}


def test_gitlab_auth_headers_missing_token():
    conn = _connector(extra_config={"token": ""})
    assert conn.auth_headers() == {"Private-Token": ""}


# --- fetch ---


@patch("requests.Session.request")
def test_gitlab_fetch_events_paginates_and_filters_since(mock_request):
    response = _make_response(
        json_data=[
            {
                "id": 1,
                "target_type": "MergeRequest",
                "action_name": "merged",
                "created_at": "2026-01-01T00:00:00.000Z",
            }
        ],
        headers={"X-Next-Page": "2"},
    )
    mock_request.return_value = response

    conn = _connector()
    events, cursor, has_more = conn.fetch_events(since="2026-01-01T00:00:00Z")

    assert len(events) == 1
    assert events[0]["id"] == 1
    assert cursor == "2"
    assert has_more is True

    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert "projects/12345/events" in args[1]
    assert kwargs["params"]["per_page"] == 100
    assert kwargs["params"]["page"] == 1
    assert kwargs["headers"]["Private-Token"] == "glpat_test"


@patch("requests.Session.request")
def test_gitlab_fetch_events_second_page_from_cursor(mock_request):
    response = _make_response(json_data=[], headers={})
    mock_request.return_value = response

    conn = _connector()
    conn.fetch_events(cursor="3")

    _, kwargs = mock_request.call_args
    assert kwargs["params"]["page"] == 3


@patch("requests.Session.request")
def test_gitlab_fetch_events_excludes_before_since(mock_request):
    response = _make_response(
        json_data=[
            {
                "id": 1,
                "target_type": "Issue",
                "created_at": "2026-01-02T00:00:00.000Z",
            },
            {
                "id": 2,
                "target_type": "Issue",
                "created_at": "2025-12-31T00:00:00.000Z",
            },
        ]
    )
    mock_request.return_value = response

    conn = _connector()
    events, cursor, has_more = conn.fetch_events(since="2026-01-01T00:00:00Z")

    assert len(events) == 1
    assert events[0]["id"] == 1
    assert cursor is None
    assert has_more is False


@patch("requests.Session.request")
def test_gitlab_fetch_events_raises_on_non_2xx(mock_request):
    response = _make_response(
        status_code=404, json_data={"message": "404 Project Not Found"}
    )
    mock_request.return_value = response

    conn = _connector()
    try:
        conn.fetch_events()
    except GitLabError as exc:
        assert "HTTP 404" in str(exc)
    else:
        raise AssertionError("Expected GitLabError on non-2xx response")


def test_gitlab_fetch_events_requires_project_id():
    conn = GitLabConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config={"token": "glpat_test"},
    )
    try:
        conn.fetch_events()
    except GitLabConfigurationError as exc:
        assert "project_id" in str(exc).lower()
    else:
        raise AssertionError("Expected GitLabConfigurationError without project_id")


# --- mapping ---


def test_gitlab_map_merge_request_merged_to_change_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 42,
                "target_type": "MergeRequest",
                "action_name": "merged",
                "created_at": "2026-01-02T00:00:00.000Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["provider"] == "gitlab"
    assert raw[0]["external_event_id"] == "gitlab:42"
    assert raw[0]["event_type"] == "CHANGE_CREATED"
    assert raw[0]["source"] == "poll"


def test_gitlab_map_merge_request_created_to_change_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 43,
                "target_type": "MergeRequest",
                "action_name": "created",
                "created_at": "2026-01-03T00:00:00.000Z",
            }
        ]
    )
    assert raw[0]["event_type"] == "CHANGE_CREATED"


def test_gitlab_map_merge_request_updated_to_change_updated():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 44,
                "target_type": "MergeRequest",
                "action_name": "updated",
                "created_at": "2026-01-04T00:00:00.000Z",
            }
        ]
    )
    assert raw[0]["event_type"] == "CHANGE_UPDATED"


def test_gitlab_map_merge_request_approved_to_review_completed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 45,
                "target_type": "MergeRequest",
                "action_name": "approved",
                "created_at": "2026-01-05T00:00:00.000Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "REVIEW_COMPLETED"


def test_gitlab_map_pipeline_running_to_build_started():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 46,
                "target_type": "Pipeline",
                "status": "running",
                "created_at": "2026-01-06T00:00:00.000Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "BUILD_STARTED"


def test_gitlab_map_pipeline_success_to_build_completed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 47,
                "target_type": "Pipeline",
                "status": "success",
                "created_at": "2026-01-07T00:00:00.000Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "BUILD_COMPLETED"


def test_gitlab_map_pipeline_failed_to_build_completed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 48,
                "target_type": "Pipeline",
                "status": "failed",
                "created_at": "2026-01-08T00:00:00.000Z",
            }
        ]
    )
    assert raw[0]["event_type"] == "BUILD_COMPLETED"


def test_gitlab_map_deployment_to_deployment_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 49,
                "target_type": "Deployment",
                "created_at": "2026-01-09T00:00:00.000Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "DEPLOYMENT_CREATED"


def test_gitlab_map_issue_to_work_item_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 50,
                "target_type": "Issue",
                "action_name": "opened",
                "created_at": "2026-01-10T00:00:00.000Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "WORK_ITEM_CREATED"


def test_gitlab_map_unknown_event_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 51,
                "target_type": "Note",
                "created_at": "2026-01-11T00:00:00.000Z",
            }
        ]
    )
    assert raw == []


def test_gitlab_map_missing_id_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "target_type": "Issue",
                "created_at": "2026-01-12T00:00:00.000Z",
            }
        ]
    )
    assert raw == []


# --- webhook ---


def test_gitlab_webhook_to_raw_events():
    conn = _connector()
    payload = {
        "event": "Merge Request",
        "id": 52,
        "action": "merge",
        "created_at": "2026-01-13T00:00:00.000Z",
    }
    raw = conn.webhook_to_raw_events(payload)
    assert len(raw) == 1
    assert raw[0]["source"] == "webhook"
    assert raw[0]["event_type"] == "CHANGE_CREATED"
    assert raw[0]["external_event_id"] == "gitlab:52"


def test_gitlab_webhook_to_raw_events_x_gitlab_event_header():
    conn = _connector()
    payload = {
        "X-Gitlab-Event": "Issue",
        "id": 53,
        "created_at": "2026-01-14T00:00:00.000Z",
    }
    raw = conn.webhook_to_raw_events(payload)
    assert len(raw) == 1
    assert raw[0]["event_type"] == "WORK_ITEM_CREATED"


def test_gitlab_webhook_signature_verification():
    conn = _connector()
    body = b'{"object_kind":"merge_request"}'
    assert conn.verify_webhook_signature(body, "whsec_test") is True
    assert conn.verify_webhook_signature(body, "wrong-secret") is False
    assert conn.verify_webhook_signature(body, None) is False
