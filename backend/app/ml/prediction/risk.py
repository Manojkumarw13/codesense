"""Risk Prediction Module."""
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from backend.app.models.ml import MLFeatureVector

class RiskPredictor:
    """Predicts risk of deployment failures and incident spikes using ML features."""
    
    def __init__(self, db: Session):
        self.db = db

    def predict_team_risk(self, team_id: uuid.UUID) -> Dict[str, Any]:
        """Predict deployment failure and incident spike risk for a given team."""
        # Get latest ML feature vector for team
        latest_vector = self.db.query(MLFeatureVector).filter(
            MLFeatureVector.team_id == team_id
        ).order_by(MLFeatureVector.period_end.desc()).first()

        if not latest_vector:
            # Fallback if no data
            return {
                "team_id": str(team_id),
                "deployment_failure_risk": 0.1,
                "incident_spike_risk": 0.1,
                "confidence": 0.0,
                "factors": ["No historical data available"]
            }

        features = latest_vector.features
        
        # Simple heuristic/probabilistic model for now based on extracted features
        # In a full implementation, we'd load the model from ModelRegistry and call .predict_proba()
        
        # Calculate deployment risk
        wip = features.get("metric_work_in_progress", 0.0)
        review_backlog = features.get("metric_review_backlog", 0.0)
        
        dep_risk = 0.05
        factors = []
        if wip > 10:
            dep_risk += 0.35
            factors.append("High Work In Progress creates deployment batching risks")
        if review_backlog > 5:
            dep_risk += 0.25
            factors.append("High Review Backlog indicates rushed code reviews")
            
        # Incident risk
        change_fail_rate = features.get("metric_change_failure_rate", 0.0)
        mttr = features.get("metric_mttr", 0.0)
        inc_risk = 0.05
        if change_fail_rate > 15.0:
            inc_risk += 0.40
            factors.append("Historically high Change Failure Rate")
        if mttr > 14400: # > 4 hours
            inc_risk += 0.20
            factors.append("High MTTR indicates struggle with resolving current issues")
            
        # Cap at 0.95
        dep_risk = min(dep_risk, 0.95)
        inc_risk = min(inc_risk, 0.95)
        
        if not factors:
            factors.append("Metrics are within healthy ranges")
            
        return {
            "team_id": str(team_id),
            "deployment_failure_risk": round(dep_risk, 2),
            "incident_spike_risk": round(inc_risk, 2),
            "confidence": 0.85,
            "factors": factors,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "period_end": latest_vector.period_end.isoformat()
        }
