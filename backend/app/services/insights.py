import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.core import Team
from backend.app.models.analytics import (
    Anomaly,
    Bottleneck,
    Insight,
    MetricDefinition
)

logger = logging.getLogger("codesense.insights")

class InsightsEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_insights_from_detections(self, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> List[Insight]:
        """Convert detected anomalies and bottlenecks into actionable insights."""
        team = self.db.query(Team).get(team_id)
        if not team:
            return []

        # Find recent detections
        recent_bottlenecks = self.db.query(Bottleneck).filter(
            Bottleneck.team_id == team_id,
            Bottleneck.detected_at >= period_start,
            Bottleneck.detected_at <= period_end
        ).all()

        recent_anomalies = self.db.query(Anomaly).filter(
            Anomaly.team_id == team_id,
            Anomaly.detected_at >= period_start,
            Anomaly.detected_at <= period_end
        ).all()

        insights = []
        now = datetime.now(timezone.utc)

        # Map bottleneck to Insight
        for b in recent_bottlenecks:
            # check if an insight for this exact bottleneck already exists
            # We can use evidence to correlate or just create a new one since it's a new period run.
            
            # Simple content generation based on deterministic rules
            content = f"Deterministic Analysis: {b.description}\n\nEvidence:\n"
            for k, v in b.evidence.items():
                content += f"- {k}: {v:.2f}% change\n"

            insight = Insight(
                id=uuid.uuid4(),
                organization_id=team.organization_id,
                team_id=team.id,
                insight_type="BOTTLENECK_EXPLANATION",
                category=b.category,
                severity=b.severity,
                title=b.title,
                content=content,
                confidence=0.9, # Deterministic rule
                evidence=b.evidence,
                generated_by="RULE_ENGINE",
                status="ACTIVE",
                created_at=now
            )
            self.db.add(insight)
            insights.append(insight)

        # Map anomalies to Insights
        for a in recent_anomalies:
            metric = self.db.query(MetricDefinition).get(a.metric_id)
            m_name = metric.name if metric else "Unknown Metric"
            
            content = f"Statistical Anomaly Detected for {m_name}.\n"
            content += f"Observed {a.observed_value:.2f} vs Baseline {a.baseline_value:.2f}.\n"
            content += f"This represents a {a.change_percent:.2f}% shift from normal patterns."

            insight = Insight(
                id=uuid.uuid4(),
                organization_id=team.organization_id,
                team_id=team.id,
                insight_type="ANOMALY_EXPLANATION",
                category="STATISTICAL",
                severity=a.severity,
                title=f"Significant deviation in {m_name}",
                content=content,
                confidence=a.confidence,
                evidence=a.evidence,
                source_metrics={"metric_id": str(a.metric_id), "metric_key": metric.metric_key if metric else None},
                generated_by="STATISTICAL_ENGINE",
                status="ACTIVE",
                created_at=now
            )
            self.db.add(insight)
            insights.append(insight)

        self.db.commit()
        return insights

    def update_insight_status(self, insight_id: uuid.UUID, new_status: str) -> Optional[Insight]:
        """Manage lifecycle: Detected -> Active -> Reviewed -> Resolved -> Archived"""
        valid_statuses = ["DETECTED", "ACTIVE", "REVIEWED", "RESOLVED", "ARCHIVED"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")
            
        insight = self.db.query(Insight).get(insight_id)
        if insight:
            insight.status = new_status
            self.db.commit()
            return insight
        return None
