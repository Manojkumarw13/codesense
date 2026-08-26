"""Feature pipeline for ML modeling."""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from backend.app.models.ml import MLFeatureVector
from backend.app.models.analytics import MetricValue, HealthScore
from backend.app.models.core import Team

logger = logging.getLogger("codesense.ml.features")

class FeatureExtractor:
    """Extracts features per period for machine learning models."""
    
    def __init__(self, db: Session):
        self.db = db

    def extract_team_features(self, team_id: str, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Extract features for a specific team and period."""
        # Query metrics
        from backend.app.models.analytics import MetricDefinition
        metrics = self.db.query(MetricValue, MetricDefinition).join(
            MetricDefinition, MetricValue.metric_id == MetricDefinition.id
        ).filter(
            MetricValue.team_id == team_id,
            MetricValue.period_start >= period_start,
            MetricValue.period_end <= period_end
        ).all()
        
        # Query health score
        health = self.db.query(HealthScore).filter(
            HealthScore.team_id == team_id,
            HealthScore.period_start >= period_start,
            HealthScore.period_end <= period_end
        ).order_by(HealthScore.calculated_at.desc()).first()

        features = {}
        for m, d in metrics:
            features[f"metric_{d.metric_key}"] = m.value
            
        if health:
            features["health_score"] = health.score
            for dim, score in health.component_metrics.items():
                features[f"health_dim_{dim}"] = score

        return features

    def run_extraction_for_period(self, period_start: datetime, period_end: datetime) -> int:
        """Run extraction for all teams."""
        teams = self.db.query(Team).all()
        extracted_count = 0
        
        for team in teams:
            features = self.extract_team_features(team.id, period_start, period_end)
            if not features:
                continue
                
            vector = MLFeatureVector(
                organization_id=team.organization_id,
                team_id=team.id,
                period_start=period_start,
                period_end=period_end,
                features=features,
                calculated_at=datetime.now(timezone.utc)
            )
            self.db.add(vector)
            extracted_count += 1
            
        self.db.commit()
        logger.info(f"Extracted features for {extracted_count} teams.")
        return extracted_count
