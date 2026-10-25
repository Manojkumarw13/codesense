"""Anomalies API - exposes statistical + ML anomalies."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.endpoints.detection_serialisation import (
    serialise_detection,
    serialise_detections,
)
from backend.app.auth.auth import AuthError, get_current_user
from backend.app.auth.dependencies import require_role, require_team_access
from backend.app.core.database import get_db
from backend.app.models.core import User
from backend.app.models.analytics import Anomaly

router = APIRouter()

REQUIRED_ROLES = [
    "ADMIN",
    "ENGINEERING_LEADER",
    "ENGINEERING_MANAGER",
    "TECH_LEAD",
    "ANALYST",
    "DEVELOPER",
]


def _current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    token = authorization[len("Bearer ") :].strip()
    try:
        return get_current_user(db, token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


def _require_role(current_user: User, db: Session) -> None:
    try:
        require_role(REQUIRED_ROLES)(current_user, db)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


def _require_team_access(current_user: User, db: Session, team_id: uuid.UUID) -> None:
    try:
        require_team_access([team_id])(current_user, db)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("/anomalies")
def list_anomalies(
    organization_id: Optional[uuid.UUID] = Query(None),
    team_id: Optional[uuid.UUID] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(_current_user),
    db: Session = Depends(get_db),
):
    """Get detected anomalies with optional filters."""
    _require_role(current_user, db)
    if team_id is not None:
        _require_team_access(current_user, db, team_id)
    q = db.query(Anomaly)
    if organization_id:
        q = q.filter(Anomaly.organization_id == organization_id)
    if team_id:
        q = q.filter(Anomaly.team_id == team_id)
    if severity:
        q = q.filter(Anomaly.severity == severity)
    total = q.count()
    items = (
        q.order_by(Anomaly.detected_at.desc(), Anomaly.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": serialise_detections(items, db),
    }


@router.get("/anomalies/{anomaly_id}")
def get_anomaly(anomaly_id: uuid.UUID, db: Session = Depends(get_db)):
    anomaly = db.query(Anomaly).get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return serialise_detection(anomaly, db)
