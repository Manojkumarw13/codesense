"""Bottlenecks API."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.analytics import Bottleneck

router = APIRouter()


@router.get("/bottlenecks")
def list_bottlenecks(
    organization_id: Optional[uuid.UUID] = Query(None),
    team_id: Optional[uuid.UUID] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get detected flow bottlenecks."""
    q = db.query(Bottleneck)
    if organization_id:
        q = q.filter(Bottleneck.organization_id == organization_id)
    if team_id:
        q = q.filter(Bottleneck.team_id == team_id)
    if category:
        q = q.filter(Bottleneck.category == category)
    if severity:
        q = q.filter(Bottleneck.severity == severity)
    total = q.count()
    items = q.order_by(Bottleneck.detected_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/bottlenecks/{bottleneck_id}")
def get_bottleneck(bottleneck_id: uuid.UUID, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    b = db.query(Bottleneck).get(bottleneck_id)
    if not b:
        raise HTTPException(status_code=404, detail="Bottleneck not found")
    return b
