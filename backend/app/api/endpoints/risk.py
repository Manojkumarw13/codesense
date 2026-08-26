"""Risk prediction API endpoints."""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.ml.prediction.risk import RiskPredictor
from backend.app.models.core import Team

router = APIRouter()

@router.get("/teams/{team_id}/risk", response_model=dict[str, Any])
def get_team_risk(team_id: uuid.UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Get risk prediction for a specific team.
    Returns probabilities for deployment failure and incident spikes.
    """
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    predictor = RiskPredictor(db)
    risk_profile = predictor.predict_team_risk(team_id)
    
    return risk_profile
