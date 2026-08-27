"""Health Score API."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.analytics import HealthScore

router = APIRouter()


@router.get("/health-score")
def list_health_scores(
    organization_id: Optional[uuid.UUID] = Query(None),
    team_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get engineering health scores (supports filtering by org/team/project)."""
    q = db.query(HealthScore)
    if organization_id:
        q = q.filter(HealthScore.organization_id == organization_id)
    if team_id:
        q = q.filter(HealthScore.team_id == team_id)
    if project_id:
        q = q.filter(HealthScore.project_id == project_id)
    total = q.count()
    items = q.order_by(HealthScore.calculated_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/health-score/{score_id}")
def get_health_score(score_id: uuid.UUID, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    hs = db.query(HealthScore).get(score_id)
    if not hs:
        raise HTTPException(status_code=404, detail="Health score not found")
    return hs
