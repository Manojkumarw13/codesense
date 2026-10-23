"""Unit tests for the GitHub provider connector (Phase 21 Task 2).

``responses`` is not installed in this environment, so HTTP tests use
``unittest.mock.patch("requests.Session.request")`` instead of
``@responses.activate`` (see task brief Step 1).
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from unittest.mock import Mock, patch

from backend.app.integrations.github import (
    GitHubConfigurationError,
    GitHubConnector,
    GitHubError,
)


def _connector(extra_config=None) -> GitHubConnector:
    config = {
        "token": "ghp_test",
        "webhook_secret": "whsec_test",
        "owner": "o",
        "repo": "r",
    }
    if extra_config:
        config.update(extra_config)
    return GitHubConnector(
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


@patch("requests.Session.request")
def test_github_fetch_events_paginates_and_filters_since(mock_request):
    response = _make_response(
        json_data=[
            {"id": 1, "type": "PullRequestEvent", "created_at": "2026-01-01T00:00:00Z"}
        ],
        headers={
            "Link": '<https://api.github.com/repos/o/r/events?page=2>; rel="next"'
        },
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
    assert "repos/o/r/events" in args[1]
    assert kwargs["params"]["per_page"] == 100
    assert kwargs["params"]["page"] == 1
    assert kwargs["headers"]["Authorization"] == "token ghp_test"


@patch("requests.Session.request")
def test_github_fetch_events_excludes_before_since(mock_request):
    response = _make_response(
        json_data=[
            {"id": 1, "type": "PullRequestEvent", "created_at": "2026-01-01T00:00:00Z"},
            {"id": 2, "type": "PullRequestEvent", "created_at": "2025-12-31T00:00:00Z"},
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
def test_github_fetch_events_raises_on_non_2xx(mock_request):
    response = _make_response(status_code=404, json_data={"message": "Not Found"})
    mock_request.return_value = response

    conn = _connector()
    try:
        conn.fetch_events()
    except GitHubError as exc:
        assert "HTTP 404" in str(exc)
    else:
        raise AssertionError("Expected GitHubError on non-2xx response")


def test_github_fetch_events_requires_owner_repo():
    conn = GitHubConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config={"token": "ghp_test"},
    )
    try:
        conn.fetch_events()
    except GitHubConfigurationError as exc:
        assert "owner" in str(exc).lower() and "repo" in str(exc).lower()
    else:
        raise AssertionError("Expected GitHubConfigurationError without owner/repo")


def test_github_map_pull_request_opened_to_change_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 42,
                "type": "PullRequestEvent",
                "action": "opened",
                "created_at": "2026-01-02T00:00:00Z",
                "pull_request": {"number": 7},
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["provider"] == "github"
    assert raw[0]["external_event_id"] == "github:42"
    assert raw[0]["event_type"] == "CHANGE_CREATED"
    assert raw[0]["source"] == "poll"


def test_github_map_pull_request_edited_to_change_updated():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 43,
                "type": "PullRequestEvent",
                "action": "edited",
                "created_at": "2026-01-03T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "CHANGE_UPDATED"


def test_github_map_pull_request_closed_to_change_updated():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 44,
                "type": "PullRequestEvent",
                "action": "closed",
                "created_at": "2026-01-04T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "CHANGE_UPDATED"


def test_github_map_check_run_started_to_build_started():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 45,
                "type": "CheckRunEvent",
                "action": "started",
                "created_at": "2026-01-05T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "BUILD_STARTED"


def test_github_map_check_run_completed_to_build_completed():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 46,
                "type": "CheckRunEvent",
                "action": "completed",
                "created_at": "2026-01-06T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "BUILD_COMPLETED"


def test_github_map_check_run_other_action_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 47,
                "type": "CheckRunEvent",
                "action": "rerequested",
                "created_at": "2026-01-07T00:00:00Z",
            }
        ]
    )
    assert raw == []


def test_github_map_deployment_to_deployment_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 48,
                "type": "DeploymentEvent",
                "created_at": "2026-01-08T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "DEPLOYMENT_CREATED"


def test_github_map_issues_to_work_item_created():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 49,
                "type": "IssuesEvent",
                "action": "opened",
                "created_at": "2026-01-09T00:00:00Z",
            }
        ]
    )
    assert len(raw) == 1
    assert raw[0]["event_type"] == "WORK_ITEM_CREATED"


def test_github_map_unknown_event_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "id": 50,
                "type": "WatchEvent",
                "created_at": "2026-01-10T00:00:00Z",
            }
        ]
    )
    assert raw == []


def test_github_map_missing_id_skipped():
    conn = _connector()
    raw = conn.map_to_raw_events(
        payloads=[
            {
                "type": "PullRequestEvent",
                "action": "opened",
                "created_at": "2026-01-11T00:00:00Z",
            }
        ]
    )
    assert raw == []


def test_github_webhook_to_raw_events():
    conn = _connector()
    payload = {
        "event": "PullRequestEvent",
        "id": 51,
        "action": "opened",
        "created_at": "2026-01-12T00:00:00Z",
        "pull_request": {"number": 3},
    }
    raw = conn.webhook_to_raw_events(payload)
    assert len(raw) == 1
    assert raw[0]["source"] == "webhook"
    assert raw[0]["event_type"] == "CHANGE_CREATED"
    assert raw[0]["external_event_id"] == "github:51"


def test_github_webhook_signature_verification():
    conn = _connector()
    body = b'{"zen":"keep it simple"}'
    sig = "sha256=" + hmac.new(b"whsec_test", body, hashlib.sha256).hexdigest()
    assert conn.verify_webhook_signature(body, sig) is True
    assert conn.verify_webhook_signature(body, "sha256=wrong") is False
    assert conn.verify_webhook_signature(body, None) is False
