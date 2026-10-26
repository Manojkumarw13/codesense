"""Provider connection API — Phase 21 Task 6.

Exposes the provider catalog, connector lifecycle (create, list, sync) and
inbound webhook ingestion on top of:

* :data:`backend.app.integrations.registry.registry` (Task 1)
* the provider connectors (Tasks 21.2–21.5)
* ``Provider`` + ``ConnectorConfig`` models and ``get_db``
* ``ingest_events_batch`` (events endpoint)
* ``BaseProviderConnector`` sync-state helpers

The connector modules are imported below so they self-register with the
registry at import time.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.endpoints.events import ingest_events_batch
from backend.app.auth.auth import AuthError, get_current_user
from backend.app.core.database import get_db
from backend.app.integrations import (  # noqa: F401  (self-register connectors)
    cicd,
    github,
    gitlab,
    jira,
)
from backend.app.integrations.base import BaseProviderConnector
from backend.app.integrations.registry import registry
from backend.app.models.configuration import ConnectorConfig, Provider
from backend.app.models.core import Organization, User
from backend.app.schemas.event import ProviderEventCreate

router = APIRouter()


def get_current_user_dep(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    """Resolve ``Authorization: Bearer <token>`` to the current active user.

    Mirrors ``auth.router._current_user`` so all authenticated endpoints share
    one resolution path (missing/invalid Bearer token -> HTTP 401).
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = authorization[len("Bearer ") :].strip()
    try:
        return get_current_user(db, token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


class ProviderItem(BaseModel):
    id: str
    name: str
    provider_type: str
    version: str | None = None
    status: str


@router.get("/providers")
def list_providers() -> dict[str, Any]:
    """List all registered provider connectors."""
    items = [
        ProviderItem(
            id=name,
            name=name,
            provider_type=name,
            version="1.0.0",
            status="active",
        )
        for name in registry.list()
    ]
    return {"items": [item.model_dump() for item in items]}


class ConnectorCreate(BaseModel):
    provider: str = Field(..., description="Registered provider name (e.g. github).")
    organization_id: uuid.UUID
    config: dict[str, Any] = Field(default_factory=dict)


def _sync_state(config: dict[str, Any] | None) -> dict[str, Any]:
    config = config or {}
    return {
        "cursor": config.get("cursor"),
        "last_synced_at": config.get("last_synced_at"),
        "status": config.get("status", "never_synced"),
        "error": config.get("error"),
    }


def _connector_row(connector: ConnectorConfig) -> dict[str, Any]:
    return {
        "id": str(connector.id),
        "provider_id": str(connector.provider_id),
        "organization_id": str(connector.organization_id),
        "config": connector.config,
        "is_enabled": connector.is_enabled,
        "last_sync_at": connector.last_sync_at,
        "sync_state": _sync_state(cast(dict[str, Any] | None, connector.config)),
        "created_at": connector.created_at,
        "updated_at": connector.updated_at,
    }


@router.post("/connectors")
def create_connector(
    connector_in: ConnectorCreate,
    current_user: User = Depends(get_current_user_dep),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Create (or reuse) a Provider and its ConnectorConfig for an organization.

    Unknown providers are rejected with HTTP 400. Re-creating the same
    (provider, organization) pair returns the existing connector (dedup) instead
    of inserting a duplicate row.
    """
    if registry.get(connector_in.provider) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider {connector_in.provider} not registered",
        )

    provider = db.query(Provider).filter(Provider.name == connector_in.provider).first()
    if provider is None:
        provider = Provider(
            name=connector_in.provider,
            provider_type=connector_in.provider,
            version=None,
            status="ACTIVE",
        )
        db.add(provider)
        db.flush()

    org = (
        db.query(Organization)
        .filter(Organization.id == connector_in.organization_id)
        .first()
    )
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    existing = (
        db.query(ConnectorConfig)
        .filter(
            ConnectorConfig.provider_id == provider.id,
            ConnectorConfig.organization_id == connector_in.organization_id,
        )
        .first()
    )
    if existing is not None:
        return _connector_row(existing)

    row = ConnectorConfig(
        provider_id=provider.id,
        organization_id=connector_in.organization_id,
        config=connector_in.config,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _connector_row(row)


@router.get("/connectors")
def list_connectors(
    organization_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user_dep),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[dict[str, Any]]:
    """List all connector configs with their sync state.

    Optionally filter by ``organization_id``.
    """
    query = db.query(ConnectorConfig)
    if organization_id is not None:
        query = query.filter(ConnectorConfig.organization_id == organization_id)
    rows = query.all()
    return [_connector_row(r) for r in rows]


@router.post("/connectors/{connector_id}/sync")
def sync_connector(
    connector_id: uuid.UUID,
    current_user: User = Depends(get_current_user_dep),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Run one sync page against the provider and ingest resulting events.

    Provider errors are reported as ``status="failed"`` with HTTP 200 (a sync
    failure is not a server error).
    """
    row = db.query(ConnectorConfig).filter(ConnectorConfig.id == connector_id).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
        )

    provider = db.query(Provider).filter(Provider.id == row.provider_id).first()
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    connector_cls = registry.get(cast(str, provider.name))
    if connector_cls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider {provider.name} not registered",
        )

    connector: BaseProviderConnector = connector_cls(
        connector_id=cast(uuid.UUID, row.id),
        org_id=cast(uuid.UUID, row.organization_id),
        config=cast(dict[str, Any], row.config),
    )

    cursor = _sync_state(cast(dict[str, Any] | None, row.config))["cursor"]
    new_config = dict(row.config)
    ingested = 0

    try:
        events, next_cursor, _ = connector.fetch_events(since=cursor)
        raw_events = connector.map_to_raw_events(payloads=events)
        ingest_list = [ProviderEventCreate(**raw) for raw in raw_events]
        result = ingest_events_batch(ingest_list, db)
        ingested = int(result.get("ingested_count", 0))
        new_config["cursor"] = next_cursor
        new_config["status"] = "synced"
        new_config["error"] = None
        new_config["last_synced_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as exc:  # noqa: BLE001  (provider error -> report failed, HTTP 200)
        new_config["status"] = "failed"
        new_config["error"] = str(exc)

    row.config = cast(Any, new_config)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "ingested": ingested,
        "sync_state": _sync_state(cast(dict[str, Any] | None, row.config)),
    }


@router.get("/connectors/{connector_id}/sync-state")
def get_sync_state(
    connector_id: uuid.UUID,
    current_user: User = Depends(get_current_user_dep),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Return the connector's sync state dict."""
    row = db.query(ConnectorConfig).filter(ConnectorConfig.id == connector_id).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
        )
    return _sync_state(cast(dict[str, Any] | None, row.config))


@router.post("/webhooks/{provider}")
async def receive_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),  # noqa: B008
):
    """Ingest an inbound provider webhook after signature verification.

    Invalid signature -> HTTP 401.
    """
    connector_cls = registry.get(provider)
    if connector_cls is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider} not registered",
        )

    row = (
        db.query(ConnectorConfig)
        .join(Provider, ConnectorConfig.provider_id == Provider.id)
        .filter(Provider.name == provider, ConnectorConfig.is_enabled == True)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No enabled connector for provider {provider}",
        )

    connector: BaseProviderConnector = connector_cls(
        connector_id=cast(uuid.UUID, row.id),
        org_id=cast(uuid.UUID, row.organization_id),
        config=cast(dict[str, Any], row.config),
    )

    body = await request.body()
    signature = (
        request.headers.get("X-Hub-Signature-256")
        or request.headers.get("X-Gitlab-Token")
        or request.headers.get("X-Webhook-Secret")
    )
    if not connector.verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload"
        )

    try:
        raw_events = connector.webhook_to_raw_events(payload)
        ingest_list = [ProviderEventCreate(**raw) for raw in raw_events]
        result = ingest_events_batch(ingest_list, db)
        return {"ingested": int(result.get("ingested_count", 0))}
    except Exception as exc:  # noqa: BLE001  (ingestion error -> report, not 500)
        return {"ingested": 0, "error": str(exc)}
