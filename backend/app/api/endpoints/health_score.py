"""Health Score API."""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.auth.auth import AuthError, get_current_user
from backend.app.auth.dependencies import require_role, require_team_access
from backend.app.core.database import get_db
from backend.app.models.analytics import HealthScore
from backend.app.models.core import User
from backend.app.privacy.policy import (
    Scope,
    count_contributors_by_scope,
    is_small_team,
    mask_evidence,
    suppression_metadata,
)

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
    """Resolve ``Authorization: Bearer <token>`` to the current active user.

    Returns 401 when the header is missing or the token is invalid.
    Mirrors the auth router's ``_current_user`` so the analytics endpoints
    stay self-contained (``auth.py`` / ``dependencies.py`` are read-only here).
    """
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
    """403 unless ``current_user`` holds one of ``REQUIRED_ROLES``."""
    try:
        require_role(REQUIRED_ROLES)(current_user, db)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


def _require_team_access(current_user: User, db: Session, team_id: uuid.UUID) -> None:
    """403 unless ``current_user`` is a member of ``team_id``."""
    try:
        require_team_access([team_id])(current_user, db)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


def _scope_base(row: HealthScore) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """The team / organisation a health score belongs to."""
    return (
        getattr(row, "team_id", None),
        getattr(row, "organization_id", None),
    )


def _period_scope(row: HealthScore) -> Scope:
    """The scope of the score's own period."""
    team_id, organization_id = _scope_base(row)
    return (
        team_id,
        organization_id,
        getattr(row, "period_start", None),
        getattr(row, "period_end", None),
    )


def _all_time_scope(row: HealthScore) -> Scope:
    """The scope of the team's whole history."""
    team_id, organization_id = _scope_base(row)
    return (team_id, organization_id, None, None)


def _effective_contributors(counts: dict[Scope, int], row: HealthScore) -> int:
    """The most conservative contributor count used for masking.

    Masking must trigger when *either* scope is below the threshold, so the
    effective count is ``min(period count, all-time count)``: a team with
    many lifetime contributors but a single contributor inside the scored
    period still has its metric evidence masked, because that period
    describes one person.
    """
    return min(counts[_period_scope(row)], counts[_all_time_scope(row)])


def _serialise_health_score(
    row: HealthScore, db: Session, contributors: int | None = None
) -> dict[str, Any]:
    """Serialise a health score, masking metric evidence for small teams.

    Masking happens at read time only: the stored ``component_metrics`` are
    never mutated, the aggregate score stays visible and only the metric
    level evidence is replaced with nulls.

    ``contributors`` is the effective (most conservative) count. It is
    optional so a single row can be serialised on its own; a page of rows
    passes the pre-computed counts in, so one query serves the whole page.
    """
    if contributors is None:
        counts = count_contributors_by_scope(
            db, [_period_scope(row), _all_time_scope(row)]
        )
        contributors = _effective_contributors(counts, row)
    component_metrics = dict(row.component_metrics or {})
    privacy: dict[str, Any] = {"suppressed": False}
    if is_small_team(contributors):
        masked: dict[str, Any] = {}
        for dimension, payload in component_metrics.items():
            if not isinstance(payload, dict):
                masked[dimension] = payload
                continue
            masked[dimension] = {
                **payload,
                "metrics": mask_evidence(payload.get("metrics")),
                "suppressed": True,
            }
        component_metrics = masked
        privacy = suppression_metadata(contributors)
    return {
        "id": str(row.id),
        "organization_id": str(row.organization_id) if row.organization_id else None,
        "team_id": str(row.team_id) if row.team_id else None,
        "project_id": str(row.project_id) if row.project_id else None,
        "period_start": row.period_start,
        "period_end": row.period_end,
        "score": row.score,
        "previous_score": row.previous_score,
        "score_change": row.score_change,
        "score_version": row.score_version,
        "component_metrics": component_metrics,
        "calculated_at": row.calculated_at,
        "privacy": privacy,
    }


@router.get("/health-score")
def list_health_scores(
    organization_id: Optional[uuid.UUID] = Query(None),
    team_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(_current_user),
    db: Session = Depends(get_db),
):
    """Get engineering health scores (supports filtering by org/team/project)."""
    _require_role(current_user, db)
    if team_id is not None:
        _require_team_access(current_user, db, team_id)
    q = db.query(HealthScore)
    if organization_id:
        q = q.filter(HealthScore.organization_id == organization_id)
    if team_id:
        q = q.filter(HealthScore.team_id == team_id)
    if project_id:
        q = q.filter(HealthScore.project_id == project_id)
    total = q.count()
    items = (
        q.order_by(HealthScore.calculated_at.desc(), HealthScore.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    scopes: list[Scope] = []
    for row in items:
        scopes.append(_period_scope(row))
        scopes.append(_all_time_scope(row))
    counts = count_contributors_by_scope(db, scopes)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            _serialise_health_score(r, db, _effective_contributors(counts, r))
            for r in items
        ],
    }


@router.get("/health-score/{score_id}")
def get_health_score(score_id: uuid.UUID, db: Session = Depends(get_db)):
    hs = db.query(HealthScore).get(score_id)
    if not hs:
        raise HTTPException(status_code=404, detail="Health score not found")
    return _serialise_health_score(hs, db)
