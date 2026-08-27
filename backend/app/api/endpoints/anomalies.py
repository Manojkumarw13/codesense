"""Anomalies API - exposes statistical + ML anomalies."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.analytics import Anomaly

router = APIRouter()


@router.get("/anomalies")
def list_anomalies(
    organization_id: Optional[uuid.UUID] = Query(None),
    team_id: Optional[uuid.UUID] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get detected anomalies with optional filters."""
    q = db.query(Anomaly)
    if organization_id:
        q = q.filter(Anomaly.organization_id == organization_id)
    if team_id:
        q = q.filter(Anomaly.team_id == team_id)
    if severity:
        q = q.filter(Anomaly.severity == severity)
    total = q.count()
    items = q.order_by(Anomaly.detected_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/anomalies/{anomaly_id}")
def get_anomaly(anomaly_id: uuid.UUID, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    anomaly = db.query(Anomaly).get(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return anomaly
