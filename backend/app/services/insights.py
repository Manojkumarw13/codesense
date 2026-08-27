import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.analytics import Anomaly, Bottleneck, Insight, MetricDefinition
from backend.app.models.core import Team

logger = logging.getLogger("codesense.insights")

class InsightsEngine:
    def __init__(self, db: Session):
        self.db = db

    def generate_insights_from_detections(self, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> list[Insight]:
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
                try:
                    # Some evidence values may be nested or non-numeric
                    if isinstance(v, (int, float)):
                        content += f"- {k}: {v:.2f}% change\n"
                    else:
                        content += f"- {k}: {v}\n"
                except Exception:
                    content += f"- {k}: {v}\n"

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
            
            # Handle ML-generated anomalies which may have None baseline/change and ML-specific evidence
            is_ml = a.evidence and isinstance(a.evidence, dict) and "ml_anomaly_score" in a.evidence
            if is_ml:
                content = f"ML Anomaly Detected for {m_name} (multivariate).\n"
                score = a.observed_value if a.observed_value is not None else a.evidence.get("ml_anomaly_score", 0)
                content += f"Anomaly score: {score:.4f} (negative => outlier).\n"
                if a.confidence is not None:
                    content += f"Confidence: {a.confidence:.2f}\n"
                top = a.evidence.get("top_contributors", {})
                if top:
                    content += "Top contributors: " + ", ".join(list(top.keys())[:3]) + ".\n"
            else:
                obs = a.observed_value if a.observed_value is not None else 0
                base = a.baseline_value if a.baseline_value is not None else 0
                chg = a.change_percent if a.change_percent is not None else 0
                content = f"Statistical Anomaly Detected for {m_name}.\n"
                content += f"Observed {obs:.2f} vs Baseline {base:.2f}.\n"
                content += f"This represents a {chg:.2f}% shift from normal patterns."

            # Determine generated_by based on evidence origin
            gen_by = "STATISTICAL_ENGINE"
            cat = "STATISTICAL"
            ins_type = "ANOMALY_EXPLANATION"
            if is_ml:
                gen_by = "ML_ENGINE"
                cat = "ML_DETECTED"
                ins_type = "ML_ANOMALY_EXPLANATION"
            insight = Insight(
                id=uuid.uuid4(),
                organization_id=team.organization_id,
                team_id=team.id,
                insight_type=ins_type,
                category=cat,
                severity=a.severity,
                title=f"Significant deviation in {m_name}" if not is_ml else f"ML anomaly: {m_name} outlier",
                content=content,
                confidence=a.confidence if a.confidence is not None else 0.6,
                evidence=a.evidence,
                source_metrics={"metric_id": str(a.metric_id), "metric_key": metric.metric_key if metric else None},
                generated_by=gen_by,
                status="ACTIVE",
                created_at=now
            )
            self.db.add(insight)
            insights.append(insight)

        self.db.commit()
        return insights

    def update_insight_status(self, insight_id: uuid.UUID, new_status: str) -> Insight | None:
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
