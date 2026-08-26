import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models.analytics import (
    Anomaly,
    Bottleneck,
    MetricDefinition,
    MetricValue,
)
from backend.app.models.core import Team

logger = logging.getLogger("codesense.detection")

class DetectionEngine:
    def __init__(self, db: Session):
        self.db = db

    def run_detection_for_period(self, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> dict[str, Any]:
        """Run both anomaly and bottleneck detection for a specific team and time period."""
        anomalies = self.detect_anomalies(team_id, period_start, period_end)
        bottlenecks = self.detect_bottlenecks(team_id, period_start, period_end)
        
        return {
            "anomalies_detected": len(anomalies),
            "bottlenecks_detected": len(bottlenecks)
        }

    def detect_anomalies(self, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> list[Anomaly]:
        team = self.db.query(Team).get(team_id)
        if not team:
            return []

        # Get current period metrics
        current_metrics = self.db.query(MetricValue).filter(
            MetricValue.team_id == team_id,
            MetricValue.period_start == period_start,
            MetricValue.period_end == period_end
        ).all()

        detected_anomalies = []
        now = datetime.now(timezone.utc)

        for val in current_metrics:
            metric = self.db.query(MetricDefinition).get(val.metric_id)
            if not metric:
                continue
            
            # Fetch historical data (e.g., last 30 periods)
            history = self.db.query(MetricValue).filter(
                MetricValue.team_id == team_id,
                MetricValue.metric_id == val.metric_id,
                MetricValue.period_end <= period_start
            ).order_by(desc(MetricValue.period_end)).limit(30).all()

            if len(history) < 3:
                # Not enough history for statistical anomaly detection, fallback to simple % change
                if val.change_percentage and abs(val.change_percentage) > 50.0:
                    severity = "MEDIUM" if abs(val.change_percentage) > 100.0 else "LOW"
                    anomaly = Anomaly(
                        id=uuid.uuid4(),
                        organization_id=team.organization_id,
                        team_id=team_id,
                        metric_id=val.metric_id,
                        severity=severity,
                        baseline_value=val.baseline_value,
                        observed_value=val.value,
                        change_percent=val.change_percentage,
                        confidence=0.5, # low confidence due to lack of history
                        evidence={"reason": "High percentage change compared to previous period", "metric_key": metric.metric_key},
                        detected_at=now
                    )
                    self.db.add(anomaly)
                    detected_anomalies.append(anomaly)
                continue

            # Calculate Z-score
            values = [h.value for h in history]
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = math.sqrt(variance)

            # Avoid division by zero
            if std_dev == 0:
                std_dev = 0.01

            z_score = abs(val.value - mean) / std_dev

            # Determine severity based on Z-score
            severity = None
            if z_score > 4.0:
                severity = "CRITICAL"
            elif z_score > 3.0:
                severity = "HIGH"
            elif z_score > 2.0:
                severity = "MEDIUM"
                
            if severity:
                change_pct = ((val.value - mean) / mean * 100.0) if mean != 0 else (100.0 if val.value > 0 else 0.0)
                anomaly = Anomaly(
                    id=uuid.uuid4(),
                    organization_id=team.organization_id,
                    team_id=team_id,
                    metric_id=val.metric_id,
                    severity=severity,
                    baseline_value=mean,
                    observed_value=val.value,
                    change_percent=change_pct,
                    confidence=min(0.95, 0.5 + (len(history) / 60.0)), # higher confidence with more history
                    evidence={"z_score": z_score, "mean": mean, "std_dev": std_dev, "history_size": len(history), "metric_key": metric.metric_key},
                    detected_at=now
                )
                self.db.add(anomaly)
                detected_anomalies.append(anomaly)

        self.db.commit()
        return detected_anomalies

    def detect_bottlenecks(self, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> list[Bottleneck]:
        team = self.db.query(Team).get(team_id)
        if not team:
            return []

        # We need recent metrics to evaluate bottleneck rules
        metrics = self.db.query(MetricValue).filter(
            MetricValue.team_id == team_id,
            MetricValue.period_start == period_start,
            MetricValue.period_end == period_end
        ).all()

        val_map = {}
        for m in metrics:
            metric = self.db.query(MetricDefinition).get(m.metric_id)
            if metric:
                 val_map[metric.metric_key] = m

        def is_increasing(metric_key: str, threshold: float = 10.0) -> bool:
            """Check if a metric is increasing significantly (> threshold%)."""
            val = val_map.get(metric_key)
            if val and val.change_percentage is not None and val.change_percentage > threshold:
                return True
            return False

        detected_bottlenecks = []
        now = datetime.now(timezone.utc)

        # 1. REVIEW Bottleneck: backlog ^ AND turnaround ^
        if is_increasing("review_backlog") and is_increasing("review_turnaround"):
            b = Bottleneck(
                id=uuid.uuid4(),
                organization_id=team.organization_id,
                team_id=team_id,
                category="REVIEW",
                severity="HIGH",
                title="Review Process Bottleneck Detected",
                description="Both review backlog and review turnaround times have increased significantly.",
                evidence={
                    "review_backlog_change": val_map["review_backlog"].change_percentage,
                    "review_turnaround_change": val_map["review_turnaround"].change_percentage
                },
                detected_at=now
            )
            detected_bottlenecks.append(b)

        # 2. CI Bottleneck: pipeline duration ^ OR failure rate ^ (build success rate v)
        # Note: build_success_rate decreasing is effectively failure rate increasing. We check if success rate is dropping.
        ci_duration_up = is_increasing("pipeline_duration")
        ci_success_down = False
        bsr = val_map.get("build_success_rate")
        if bsr and bsr.change_percentage is not None and bsr.change_percentage < -10.0:
            ci_success_down = True

        if ci_duration_up or ci_success_down:
            evidence = {}
            if ci_duration_up: evidence["pipeline_duration_change"] = val_map["pipeline_duration"].change_percentage
            if ci_success_down: evidence["build_success_rate_change"] = val_map["build_success_rate"].change_percentage
            
            b = Bottleneck(
                id=uuid.uuid4(),
                organization_id=team.organization_id,
                team_id=team_id,
                category="CI",
                severity="MEDIUM" if not (ci_duration_up and ci_success_down) else "HIGH",
                title="CI Pipeline Bottleneck Detected",
                description="CI pipeline duration has increased or success rate has dropped.",
                evidence=evidence,
                detected_at=now
            )
            detected_bottlenecks.append(b)

        # 3. DEPLOYMENT Bottleneck: deployment failure ^
        if is_increasing("deployment_failure_rate"):
            b = Bottleneck(
                id=uuid.uuid4(),
                organization_id=team.organization_id,
                team_id=team_id,
                category="DEPLOYMENT",
                severity="HIGH",
                title="Deployment Reliability Bottleneck Detected",
                description="Deployment failure rate has increased significantly.",
                evidence={
                    "deployment_failure_rate_change": val_map["deployment_failure_rate"].change_percentage
                },
                detected_at=now
            )
            detected_bottlenecks.append(b)

        # 4. WORKFLOW Bottleneck: WIP ^ AND cycle time ^
        if is_increasing("work_in_progress") and is_increasing("cycle_time"):
            b = Bottleneck(
                id=uuid.uuid4(),
                organization_id=team.organization_id,
                team_id=team_id,
                category="WORKFLOW",
                severity="HIGH",
                title="Workflow & WIP Bottleneck Detected",
                description="Work in progress and overall cycle time have both increased.",
                evidence={
                    "work_in_progress_change": val_map["work_in_progress"].change_percentage,
                    "cycle_time_change": val_map["cycle_time"].change_percentage
                },
                detected_at=now
            )
            detected_bottlenecks.append(b)

        for dbot in detected_bottlenecks:
            self.db.add(dbot)
            
        self.db.commit()
        return detected_bottlenecks
