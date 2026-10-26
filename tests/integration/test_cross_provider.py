"""Cross-provider validation test — Phase 21 Task 7.

Verifies that GitHub pull_request opened and GitLab merge_request opened both
map to the same canonical event type (CHANGE_CREATED), and that re-ingesting
identical events deduplicates by provider + external_event_id.

TDD: run with:

    cd /home/manoj/Project/CodeSense/.worktrees/phases20-29
    /home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/integration/test_cross_provider.py -q
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from backend.app.api.endpoints.events import ingest_events_batch
from backend.app.core.database import SessionLocal
from backend.app.integrations.github import GitHubConnector
from backend.app.integrations.gitlab import GitLabConnector
from backend.app.models.core import CanonicalEvent, Organization
from backend.app.models.raw import ProviderEvent
from backend.app.schemas.event import ProviderEventCreate
from backend.app.services.processing import EventProcessor


@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_tables(db):
    """Keep tables touched by this file isolated between tests."""
    yield
    db.execute(text("DELETE FROM core.canonical_events"))
    db.execute(text("DELETE FROM raw.provider_events"))
    db.execute(text("DELETE FROM core.organizations"))
    db.commit()


def test_github_and_gitlab_produce_same_canonical_event_type(db):
    org = Organization(name="Cross-Provider Test Org")
    db.add(org)
    db.commit()
    db.refresh(org)

    gh_conn = GitHubConnector(connector_id=uuid4(), org_id=org.id, config={})
    gl_conn = GitLabConnector(connector_id=uuid4(), org_id=org.id, config={})

    gh_payload = {
        "type": "pull_request",
        "action": "opened",
        "id": 101,
        "created_at": "2026-01-15T10:00:00+00:00",
        "number": 101,
        "title": "Add cross-provider validation",
    }
    gl_payload = {
        "type": "Merge Request",
        "action_name": "opened",
        "id": 202,
        "created_at": "2026-01-15T11:00:00+00:00",
    }

    # 1+2. Map both via their connectors to raw events.
    gh_raw = gh_conn.map_to_raw_events(payloads=[gh_payload])
    gl_raw = gl_conn.map_to_raw_events(payloads=[gl_payload])
    assert len(gh_raw) == 1 and gh_raw[0]["event_type"] == "CHANGE_CREATED"
    assert len(gl_raw) == 1 and gl_raw[0]["event_type"] == "CHANGE_CREATED"
    assert gh_raw[0]["provider"] == "github"
    assert gl_raw[0]["provider"] == "gitlab"

    # 3. Ingest both via ingest_events_batch.
    ingest_list = [ProviderEventCreate(**raw) for raw in gh_raw + gl_raw]
    result = ingest_events_batch(ingest_list, db)
    assert result["ingested_count"] == 2, result

    # 4. Run EventProcessor.
    processor = EventProcessor(db)
    processed = processor.process_pending_events()
    assert processed == 2

    # 5. Both raw events produced a CanonicalEvent with event_type == CHANGE_CREATED.
    canon = (
        db.query(CanonicalEvent)
        .filter(CanonicalEvent.event_type == "CHANGE_CREATED")
        .all()
    )
    assert len(canon) == 2

    # 6. Dedup: ingesting the same GitHub event twice yields one raw row.
    result2 = ingest_events_batch([ProviderEventCreate(**gh_raw[0])], db)
    assert result2["ingested_count"] == 0
    assert result2["results"][0]["status"] == "ignored_duplicate"

    raw_rows = (
        db.query(ProviderEvent)
        .filter_by(provider="github", external_event_id="github:101")
        .all()
    )
    assert len(raw_rows) == 1
