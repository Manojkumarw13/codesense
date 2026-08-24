import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.core import Team
from backend.app.models.analytics import (
    MetricValue,
    HealthScore,
    HealthScoreComponent,
    MetricDefinition
)
from backend.app.models.configuration import HealthScoreConfig

logger = logging.getLogger("codesense.health")

class HealthScoreEngine:
    DEFAULT_WEIGHTS = {
        "Delivery Flow": 0.20,
        "Development Flow": 0.20,
        "Review Flow": 0.15,
        "CI/CD Reliability": 0.15,
        "Deployment Health": 0.15,
        "Operational Health": 0.15,
    }

    # Map dimensions to the metric keys that compose them
    DIMENSION_METRICS = {
        "Delivery Flow": ["deployment_frequency", "lead_time", "cycle_time"],
        "Development Flow": ["pr_cycle_time", "work_in_progress"],
        "Review Flow": ["review_turnaround", "review_backlog"],
        "CI/CD Reliability": ["build_success_rate", "pipeline_duration"],
        "Deployment Health": ["deployment_failure_rate"],
        "Operational Health": ["change_failure_rate", "mttr"],
    }

    def __init__(self, db: Session):
        self.db = db

    def _get_configs(self, organization_id: uuid.UUID) -> Dict[str, HealthScoreConfig]:
        configs = self.db.query(HealthScoreConfig).filter(
            HealthScoreConfig.organization_id == organization_id,
            HealthScoreConfig.is_enabled == True
        ).all()
        
        config_map = {c.dimension: c for c in configs}
        
        # Ensure default configs exist for missing dimensions
        for dim, default_weight in self.DEFAULT_WEIGHTS.items():
            if dim not in config_map:
                cfg = HealthScoreConfig(
                    id=uuid.uuid4(),
                    organization_id=organization_id,
                    dimension=dim,
                    weight=default_weight
                )
                self.db.add(cfg)
                config_map[dim] = cfg
        self.db.commit()
        
        return config_map

    def _normalize_metric(self, metric_key: str, value: float) -> float:
        # Simple normalization heuristics for MVP (0 to 100)
        # In a full system, this would be based on configurable baseline/goals.
        
        # Higher is better
        if metric_key in ["deployment_frequency", "build_success_rate"]:
            if metric_key == "build_success_rate":
                return min(100.0, max(0.0, value))
            elif metric_key == "deployment_frequency":
                return min(100.0, (value / 10.0) * 100.0) # Assuming 10 per period is 100
        
        # Lower is better
        elif metric_key in [
            "lead_time", "cycle_time", "pr_cycle_time", "review_turnaround", 
            "pipeline_duration", "mttr"
        ]:
            # Convert seconds to hours for heuristic
            hours = value / 3600.0
            if metric_key in ["pr_cycle_time", "review_turnaround"]:
                return max(0.0, 100.0 - (hours * 2.0)) # 50 hours = 0
            else:
                return max(0.0, 100.0 - (hours))
                
        elif metric_key in ["deployment_failure_rate", "change_failure_rate"]:
            return max(0.0, 100.0 - value)
            
        elif metric_key in ["review_backlog", "work_in_progress"]:
            return max(0.0, 100.0 - (value * 5.0)) # 20 items = 0
            
        return 50.0 # fallback

    def calculate_health_score(self, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> HealthScore:
        team = self.db.query(Team).get(team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")

        org_id = team.organization_id
        configs = self._get_configs(org_id)
        
        # Get metrics for this team and period
        metric_values = self.db.query(MetricValue).join(MetricDefinition).filter(
            MetricValue.team_id == team_id,
            MetricValue.period_start == period_start,
            MetricValue.period_end == period_end
        ).all()
        
        val_map = {v.metric.metric_key: v for v in metric_values if hasattr(v, 'metric') and v.metric}
        # In case we can't join easily, fetch definitions and map
        if not val_map:
            defs = self.db.query(MetricDefinition).all()
            def_map = {d.id: d.metric_key for d in defs}
            val_map = {def_map[v.metric_id]: v for v in metric_values if v.metric_id in def_map}

        component_records = []
        overall_score = 0.0
        total_weight = 0.0
        component_metrics_json = {}

        for dim, cfg in configs.items():
            if cfg.weight <= 0:
                continue
                
            dim_metrics = self.DIMENSION_METRICS.get(dim, [])
            dim_score_sum = 0.0
            metrics_count = 0
            evidence = {}
            
            for m_key in dim_metrics:
                if m_key in val_map:
                    val_record = val_map[m_key]
                    raw_val = val_record.value
                    norm_val = self._normalize_metric(m_key, raw_val)
                    dim_score_sum += norm_val
                    metrics_count += 1
                    evidence[m_key] = {
                        "raw_value": raw_val,
                        "normalized": norm_val,
                        "metric_id": str(val_record.metric_id)
                    }
                    
            if metrics_count > 0:
                dim_score = dim_score_sum / metrics_count
                contrib = dim_score * cfg.weight
                overall_score += contrib
                total_weight += cfg.weight
                
                comp = HealthScoreComponent(
                    id=uuid.uuid4(),
                    dimension=dim,
                    score=dim_score,
                    weight=cfg.weight,
                    contribution=contrib
                )
                component_records.append(comp)
                component_metrics_json[dim] = {
                    "score": dim_score,
                    "weight": cfg.weight,
                    "metrics": evidence
                }
                
        if total_weight > 0 and total_weight < 1.0:
             # scale to 100 if weights don't add up to 1
             overall_score = overall_score / total_weight

        # Check for previous score
        duration = period_end - period_start
        prev_start = period_start - duration
        prev_end = period_start
        
        prev_hs = self.db.query(HealthScore).filter(
            HealthScore.team_id == team_id,
            HealthScore.period_start == prev_start,
            HealthScore.period_end == prev_end
        ).first()
        
        previous_score = prev_hs.score if prev_hs else None
        score_change = (overall_score - previous_score) if previous_score is not None else None
        
        # Create HealthScore record
        hs = HealthScore(
            id=uuid.uuid4(),
            organization_id=org_id,
            team_id=team_id,
            period_start=period_start,
            period_end=period_end,
            score=overall_score,
            previous_score=previous_score,
            score_change=score_change,
            component_metrics=component_metrics_json
        )
        self.db.add(hs)
        self.db.commit() # Commit to get ID if needed
        
        for comp in component_records:
            comp.health_score_id = hs.id
            self.db.add(comp)
            
        self.db.commit()
        return hs
