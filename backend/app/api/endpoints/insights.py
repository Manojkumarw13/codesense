"""Insights API."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.endpoints.detection_serialisation import (
    serialise_detection,
    serialise_detections,
)
from backend.app.api.auth_deps import (
    REQUIRED_ROLES,
    require_auth,
    require_team_access_if,
)
from backend.app.core.database import get_db
from backend.app.models.core import User
from backend.app.models.analytics import Insight

router = APIRouter()


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
    current_user: User = Depends(require_auth(REQUIRED_ROLES)),
    db: Session = Depends(get_db),
):
    """Get engineering/AI insights with evidence and confidence."""
    require_team_access_if(current_user, db, team_id)
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
        "items": serialise_detections(items, db),
    }


@router.get("/insights/{insight_id}")
def get_insight(insight_id: uuid.UUID, db: Session = Depends(get_db)):
    ins = db.query(Insight).get(insight_id)
    if not ins:
        raise HTTPException(status_code=404, detail="Insight not found")
    return serialise_detection(ins, db)
