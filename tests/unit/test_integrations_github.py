"""Unit tests for the GitHub provider connector (Phase 21 Task 2).

``responses`` is not installed in this environment, so the HTTP test uses
``unittest.mock.patch("requests.Session.request")`` instead of
``@responses.activate`` (see task brief Step 1).
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from unittest.mock import Mock, patch

from backend.app.integrations.github import GitHubConnector


def _connector() -> GitHubConnector:
    return GitHubConnector(
        connector_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        config={"token": "ghp_test", "webhook_secret": "whsec_test"},
    )


@patch("requests.Session.request")
def test_github_fetch_events_paginates_and_filters_since(mock_request):
    response = Mock()
    response.status_code = 200
    response.json.return_value = [
        {"id": 1, "type": "PullRequestEvent", "created_at": "2026-01-01T00:00:00Z"}
    ]
    response.headers = {
        "Link": '<https://api.github.com/repos/o/r/events?page=2>; rel="next"'
    }
    mock_request.return_value = response

    conn = _connector()
    events, cursor, has_more = conn.fetch_events(since="2026-01-01T00:00:00Z")

    assert len(events) == 1
    assert events[0]["id"] == 1
    assert cursor == "2"
    assert has_more is True

    # The request must hit the GitHub REST events endpoint with per_page=100.
    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert "repos/o/r/events" in args[1]
    assert kwargs["params"]["per_page"] == 100
    assert kwargs["params"]["page"] == 1
    assert kwargs["headers"]["Authorization"] == "token ghp_test"


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


def test_github_webhook_signature_verification():
    conn = _connector()
    body = b'{"zen":"keep it simple"}'
    sig = "sha256=" + hmac.new(b"whsec_test", body, hashlib.sha256).hexdigest()
    assert conn.verify_webhook_signature(body, sig) is True
    assert conn.verify_webhook_signature(body, "sha256=wrong") is False
