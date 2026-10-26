"""Provider connection API integration tests — Phase 21 Task 6.

TDD: these tests define the behaviour of ``backend/app/api/endpoints/providers.py``
before it exists. Run with:

    cd /home/manoj/Project/CodeSense/.worktrees/phases20-29
    /home/manoj/Project/CodeSense/.venv/bin/python -m pytest tests/integration/test_provider_api.py -q
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.auth.auth import create_access_token
from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.configuration import ConnectorConfig, Provider
from backend.app.models.core import Organization, User

client = TestClient(app)


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
    db.execute(text("DELETE FROM raw.provider_events"))
    db.execute(text("DELETE FROM configuration.connector_configs"))
    db.execute(text("DELETE FROM configuration.providers"))
    db.execute(text("DELETE FROM core.organizations"))
    db.commit()


def create_org(db, name="Test Org"):
    org = Organization(name=name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def create_provider(
    db, name="github", provider_type="git", version="1.0.0", status="ACTIVE"
):
    provider = Provider(
        name=name, provider_type=provider_type, version=version, status=status
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def create_connector(db, provider, org, config=None):
    row = ConnectorConfig(
        provider_id=provider.id,
        organization_id=org.id,
        config=config or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _auth_header(db) -> dict[str, str]:
    """Seed an org + active user and return Bearer auth headers."""
    user_id = uuid.uuid4()
    org = Organization(name="Auth Org")
    db.add(org)
    db.flush()
    user = User(
        id=user_id,
        organization_id=org.id,
        email=f"connector-auth-{user_id}@example.com",
        password_hash=bcrypt.hashpw(b"x", bcrypt.gensalt()).decode(),
        status="ACTIVE",
    )
    db.add(user)
    db.commit()
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Providers catalog
# ---------------------------------------------------------------------------


def test_providers_list_includes_registered():
    resp = client.get("/api/v1/providers")
    assert resp.status_code == 200, resp.text
    names = {p["name"] for p in resp.json()["items"]}
    assert {"github", "gitlab", "jira", "cicd"} <= names
    for p in resp.json()["items"]:
        assert {"id", "name", "provider_type", "version", "status"} <= set(p.keys())


# ---------------------------------------------------------------------------
# Connector create / list
# ---------------------------------------------------------------------------


def test_connector_create_and_list(db):
    org = create_org(db)
    payload = {
        "provider": "github",
        "organization_id": str(org.id),
        "config": {"token": "tok", "webhook_secret": "sec", "owner": "o", "repo": "r"},
    }
    resp = client.post("/api/v1/connectors", json=payload, headers=_auth_header(db))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["config"]["token"] == "tok"
    assert body["sync_state"]["status"] == "never_synced"

    # Provider was created (or reused) in the DB
    provider = db.query(Provider).filter(Provider.name == "github").first()
    assert provider is not None

    resp = client.get("/api/v1/connectors", headers=_auth_header(db))
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) >= 1
    assert "sync_state" in items[0]
    assert items[0]["config"]["token"] == "tok"


# ---------------------------------------------------------------------------
# Connector sync
# ---------------------------------------------------------------------------


class _FailingConnector:
    def __init__(self, connector_id, org_id, config):
        self.config = dict(config or {})

    def fetch_events(self, since=None, cursor=None):
        raise RuntimeError("provider is down")


@patch("backend.app.api.endpoints.providers.registry.get")
def test_connector_sync_returns_failed_state_on_provider_error(mock_get, db):
    org = create_org(db)
    provider = create_provider(db, "github")
    connector = create_connector(
        db, provider, org, config={"cursor": "1", "token": "x"}
    )

    mock_get.return_value = _FailingConnector

    resp = client.post(
        f"/api/v1/connectors/{connector.id}/sync", headers=_auth_header(db)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ingested"] == 0
    assert body["sync_state"]["status"] == "failed"
    assert "provider is down" in body["sync_state"]["error"]

    # Failure persisted on the ConnectorConfig
    db.refresh(connector)
    assert connector.config["status"] == "failed"
    assert "provider is down" in connector.config["error"]


class _OkConnector:
    def __init__(self, connector_id, org_id, config):
        self.config = dict(config or {})

    def fetch_events(self, since=None, cursor=None):
        return [{"id": 1, "created_at": "2026-01-01T00:00:00+00:00"}], "2", True

    def map_to_raw_events(
        self, team_id=None, project_id=None, repo_id=None, payloads=None
    ):
        return [
            {
                "provider": "github",
                "external_event_id": "github:1",
                "event_type": "CHANGE_CREATED",
                "event_timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "payload": {"id": 1},
                "source": "poll",
            }
        ]


@patch("backend.app.api.endpoints.providers.registry.get")
def test_connector_sync_success_updates_sync_state(mock_get, db):
    org = create_org(db)
    provider = create_provider(db, "github")
    connector = create_connector(db, provider, org, config={"token": "x"})

    mock_get.return_value = _OkConnector

    resp = client.post(
        f"/api/v1/connectors/{connector.id}/sync", headers=_auth_header(db)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ingested"] == 1
    assert body["sync_state"]["cursor"] == "2"
    assert body["sync_state"]["status"] == "synced"
    assert body["sync_state"]["error"] is None

    db.refresh(connector)
    assert connector.config["cursor"] == "2"
    assert connector.config["status"] == "synced"


# ---------------------------------------------------------------------------
# Connector sync state
# ---------------------------------------------------------------------------


def test_connector_sync_state_get(db):
    org = create_org(db)
    provider = create_provider(db, "github")
    connector = create_connector(
        db,
        provider,
        org,
        config={
            "cursor": "3",
            "last_synced_at": "2026-01-01T00:00:00+00:00",
            "status": "synced",
            "error": None,
        },
    )

    resp = client.get(
        f"/api/v1/connectors/{connector.id}/sync-state", headers=_auth_header(db)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "cursor": "3",
        "last_synced_at": "2026-01-01T00:00:00+00:00",
        "status": "synced",
        "error": None,
    }


# ---------------------------------------------------------------------------
# Auth guard: unauthenticated calls to management endpoints must be rejected.


def test_connector_create_requires_authentication(db):
    org = create_org(db)
    payload = {
        "provider": "github",
        "organization_id": str(org.id),
        "config": {},
    }
    resp = client.post("/api/v1/connectors", json=payload)
    assert resp.status_code == 401, resp.text


def test_connectors_list_requires_authentication(db):
    resp = client.get("/api/v1/connectors")
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


class _BadSigConnector:
    def __init__(self, connector_id, org_id, config):
        self.config = dict(config or {})

    def verify_webhook_signature(self, payload, signature=None):
        return False


@patch("backend.app.api.endpoints.providers.registry.get")
def test_webhook_invalid_signature_returns_401(mock_get, db):
    org = create_org(db)
    provider = create_provider(db, "github")
    create_connector(db, provider, org, config={"webhook_secret": "secret"})

    mock_get.return_value = _BadSigConnector

    resp = client.post(
        "/api/v1/webhooks/github",
        content=b"{}",
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )
    assert resp.status_code == 401, resp.text


class _OkWebhookConnector:
    def __init__(self, connector_id, org_id, config):
        self.config = dict(config or {})

    def verify_webhook_signature(self, payload, signature=None):
        return True

    def webhook_to_raw_events(self, payload):
        return [
            {
                "provider": "github",
                "external_event_id": "github:wh-1",
                "event_type": "CHANGE_CREATED",
                "event_timestamp": None,
                "payload": payload,
                "source": "webhook",
            }
        ]


@patch("backend.app.api.endpoints.providers.registry.get")
def test_webhook_success_ingests_events(mock_get, db):
    org = create_org(db)
    provider = create_provider(db, "github")
    create_connector(db, provider, org, config={"webhook_secret": "secret"})

    mock_get.return_value = _OkWebhookConnector

    resp = client.post(
        "/api/v1/webhooks/github",
        json={"event": "push", "id": 1},
        headers={"X-Hub-Signature-256": "sha256=good"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ingested": 1}


# ---------------------------------------------------------------------------
# Fix round 1: dedup, org filter, unknown provider, webhook error handling
# ---------------------------------------------------------------------------


def test_connector_create_dedup_same_provider_org(db):
    """Re-creating the same (provider, organization) returns the same row."""
    org = create_org(db)
    payload = {
        "provider": "github",
        "organization_id": str(org.id),
        "config": {"token": "tok", "owner": "o", "repo": "r"},
    }
    resp1 = client.post("/api/v1/connectors", json=payload, headers=_auth_header(db))
    assert resp1.status_code == 200, resp1.text
    first_id = resp1.json()["id"]

    resp2 = client.post("/api/v1/connectors", json=payload, headers=_auth_header(db))
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["id"] == first_id

    # No duplicate rows in the DB
    rows = db.query(ConnectorConfig).all()
    assert len(rows) == 1
    assert str(rows[0].id) == first_id


def test_connector_create_unknown_provider_returns_400(db):
    org = create_org(db)
    payload = {
        "provider": "no-such-provider",
        "organization_id": str(org.id),
        "config": {},
    }
    resp = client.post("/api/v1/connectors", json=payload, headers=_auth_header(db))
    assert resp.status_code == 400, resp.text


def test_list_connectors_filters_by_organization(db):
    org1 = create_org(db, name="Org One")
    org2 = create_org(db, name="Org Two")
    provider = create_provider(db, "github")

    c1 = create_connector(db, provider, org1, config={"token": "a"})
    create_connector(db, provider, org2, config={"token": "b"})

    resp = client.get(
        f"/api/v1/connectors?organization_id={org1.id}", headers=_auth_header(db)
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == str(c1.id)


class _FailingWebhookConnector:
    def __init__(self, connector_id, org_id, config):
        self.config = dict(config or {})

    def verify_webhook_signature(self, payload, signature=None):
        return True

    def webhook_to_raw_events(self, payload):
        raise RuntimeError("webhook mapping failed")


@patch("backend.app.api.endpoints.providers.registry.get")
def test_webhook_ingestion_error_returns_structured_not_500(mock_get, db):
    org = create_org(db)
    provider = create_provider(db, "github")
    create_connector(db, provider, org, config={"webhook_secret": "secret"})

    mock_get.return_value = _FailingWebhookConnector

    resp = client.post(
        "/api/v1/webhooks/github",
        json={"event": "push", "id": 1},
        headers={"X-Hub-Signature-256": "sha256=good"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ingested"] == 0
    assert "error" in body
    assert "webhook mapping failed" in body["error"]
