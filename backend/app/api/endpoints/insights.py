"""Insights API."""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.analytics import Insight
from backend.app.privacy.policy import (
    count_contributors,
    is_small_team,
    mask_evidence,
    suppression_metadata,
)

router = APIRouter()


def _optional_id(value: Any) -> str | None:
    """Render an optional UUID column as a string."""
    return str(value) if value is not None else None


def _serialise(row: Any, db: Session) -> dict[str, Any]:
    """Serialise a detection row, masking evidence for small teams.

    Every column the row actually has is kept, so the response keeps its
    previous shape; only the metric level evidence is replaced with nulls
    and a ``privacy`` block explains the decision.
    """
    contributors = count_contributors(
        db,
        getattr(row, "team_id", None),
        organization_id=getattr(row, "organization_id", None),
    )
    privacy: dict[str, Any] = {"suppressed": False}
    evidence = getattr(row, "evidence", None)
    if is_small_team(contributors):
        evidence = mask_evidence(evidence)
        privacy = suppression_metadata(contributors)
    return {
        "id": str(row.id),
        "organization_id": _optional_id(getattr(row, "organization_id", None)),
        "team_id": _optional_id(getattr(row, "team_id", None)),
        "project_id": _optional_id(getattr(row, "project_id", None)),
        "request_id": _optional_id(getattr(row, "request_id", None)),
        "metric_id": _optional_id(getattr(row, "metric_id", None)),
        "insight_type": getattr(row, "insight_type", None),
        "category": getattr(row, "category", None),
        "severity": getattr(row, "severity", None),
        "title": getattr(row, "title", None),
        "description": getattr(row, "description", None),
        "content": getattr(row, "content", None),
        "confidence": getattr(row, "confidence", None),
        "generated_by": getattr(row, "generated_by", None),
        "status": getattr(row, "status", None),
        "baseline_value": getattr(row, "baseline_value", None),
        "observed_value": getattr(row, "observed_value", None),
        "change_percent": getattr(row, "change_percent", None),
        "evidence": evidence,
        "source_metrics": getattr(row, "source_metrics", None),
        "detected_at": getattr(row, "detected_at", None),
        "created_at": getattr(row, "created_at", None),
        "privacy": privacy,
    }


@router.get("/insights")
def list_insights(
    organization_id: Optional[uuid.UUID] = Query(None),
    team_id: Optional[uuid.UUID] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    generated_by: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get engineering/AI insights with evidence and confidence."""
    q = db.query(Insight)
    if organization_id:
        q = q.filter(Insight.organization_id == organization_id)
    if team_id:
        q = q.filter(Insight.team_id == team_id)
    if category:
        q = q.filter(Insight.category == category)
    if severity:
        q = q.filter(Insight.severity == severity)
    if status:
        q = q.filter(Insight.status == status)
    if generated_by:
        q = q.filter(Insight.generated_by == generated_by)
    total = q.count()
    items = (
        q.order_by(Insight.created_at.desc(), Insight.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [_serialise(r, db) for r in items],
    }


@router.get("/insights/{insight_id}")
def get_insight(insight_id: uuid.UUID, db: Session = Depends(get_db)):
    ins = db.query(Insight).get(insight_id)
    if not ins:
        raise HTTPException(status_code=404, detail="Insight not found")
    return _serialise(ins, db)
