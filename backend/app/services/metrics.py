import logging
import uuid
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models.analytics import MetricDefinition, MetricValue
from backend.app.models.core import (
    Build,
    Change,
    Deployment,
    Incident,
    Review,
    Team,
    WorkItem,
)

logger = logging.getLogger("codesense.metrics")

class MetricEngine:
    def __init__(self, db: Session):
        self.db = db
        self._ensure_definitions()

    def _ensure_definitions(self):
        definitions = [
            ("deployment_frequency", "Deployment Frequency", "Delivery", "deployments/period", "count"),
            ("lead_time", "Lead Time for Changes", "Delivery", "seconds", "average"),
            ("cycle_time", "Cycle Time", "Delivery", "seconds", "average"),
            ("pr_cycle_time", "PR/MR Cycle Time", "Development", "seconds", "average"),
            ("review_turnaround", "Review Turnaround", "Development", "seconds", "average"),
            ("review_backlog", "Review Backlog", "Development", "count", "average"),
            ("build_success_rate", "Build Success Rate", "CI/CD", "percentage", "average"),
            ("pipeline_duration", "Pipeline Duration", "CI/CD", "seconds", "average"),
            ("deployment_failure_rate", "Deployment Failure Rate", "Deployment", "percentage", "average"),
            ("change_failure_rate", "Change Failure Rate", "Reliability", "percentage", "average"),
            ("mttr", "MTTR", "Reliability", "seconds", "average"),
            ("work_in_progress", "Work-in-Progress", "Workflow", "count", "average"),
        ]
        
        from sqlalchemy.dialects.postgresql import insert
        
        self.metric_defs = {}
        for key, name, category, unit, agg in definitions:
            stmt = insert(MetricDefinition).values(
                id=uuid.uuid4(),
                metric_key=key,
                name=name,
                category=category,
                unit=unit,
                aggregation_method=agg
            ).on_conflict_do_nothing(index_elements=['metric_key'])
            self.db.execute(stmt)
            self.db.commit()
            
            dfn = self.db.query(MetricDefinition).filter(MetricDefinition.metric_key == key).first()
            self.metric_defs[key] = dfn

    def calculate_metrics_for_period(self, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> list[MetricValue]:
        values = []
        
        # 1. Deployment Frequency
        deployments = self.db.query(Deployment).filter(
            Deployment.team_id == team_id,
            Deployment.completed_at >= period_start,
            Deployment.completed_at < period_end,
            Deployment.status == "SUCCESS"
        ).count()
        values.append(self._create_value("deployment_frequency", float(deployments), team_id, period_start, period_end))
        
        # 2. Lead Time for Changes (deployment_time - change_start_time)
        # We need deployments linked to changes
        lt_records = self.db.query(Deployment, Change).join(Change, Deployment.change_id == Change.id).filter(
            Deployment.team_id == team_id,
            Deployment.completed_at >= period_start,
            Deployment.completed_at < period_end,
            Deployment.status == "SUCCESS",
            Change.created_at != None
        ).all()
        if lt_records:
            total_seconds = sum((d.completed_at - c.created_at).total_seconds() for d, c in lt_records if d.completed_at and c.created_at)
            values.append(self._create_value("lead_time", total_seconds / len(lt_records), team_id, period_start, period_end))
        
        # 3. Cycle Time (completion_time - work_start_time)
        ct_records = self.db.query(WorkItem).filter(
            WorkItem.team_id == team_id,
            WorkItem.completed_at >= period_start,
            WorkItem.completed_at < period_end,
            WorkItem.started_at != None
        ).all()
        if ct_records:
            total_seconds = sum((w.completed_at - w.started_at).total_seconds() for w in ct_records if w.completed_at and w.started_at)
            values.append(self._create_value("cycle_time", total_seconds / len(ct_records), team_id, period_start, period_end))
            
        # 4. PR/MR Cycle Time (merge_time - creation_time)
        pr_records = self.db.query(Change).filter(
            Change.team_id == team_id,
            Change.merged_at >= period_start,
            Change.merged_at < period_end,
            Change.created_at != None
        ).all()
        if pr_records:
            total_seconds = sum((c.merged_at - c.created_at).total_seconds() for c in pr_records if c.merged_at and c.created_at)
            values.append(self._create_value("pr_cycle_time", total_seconds / len(pr_records), team_id, period_start, period_end))
            
        # 5. Review Turnaround (review_completion - review_request)
        # Assuming requested_at and completed_at exist in Review model
        rev_records = self.db.query(Review).join(Change, Review.change_id == Change.id).filter(
            Change.team_id == team_id,
            Review.completed_at >= period_start,
            Review.completed_at < period_end,
            Review.requested_at != None
        ).all()
        if rev_records:
            total_seconds = sum((r.completed_at - r.requested_at).total_seconds() for r in rev_records if r.completed_at and r.requested_at)
            values.append(self._create_value("review_turnaround", total_seconds / len(rev_records), team_id, period_start, period_end))
            
        # 6. Review Backlog (# changes awaiting review in period)
        # This is typically an active count at period end or average. We'll use count of reviews still pending at period_end.
        # Simplification: Reviews requested before period_end, but not completed before period_end.
        backlog_count = self.db.query(Review).join(Change, Review.change_id == Change.id).filter(
            Change.team_id == team_id,
            Review.requested_at < period_end,
            or_(Review.completed_at == None, Review.completed_at >= period_end)
        ).count()
        values.append(self._create_value("review_backlog", float(backlog_count), team_id, period_start, period_end))

        # 7. Build Success Rate (successful_builds / total_builds)
        total_builds = self.db.query(Build).filter(
            Build.team_id == team_id,
            Build.completed_at >= period_start,
            Build.completed_at < period_end
        ).count()
        if total_builds > 0:
            success_builds = self.db.query(Build).filter(
                Build.team_id == team_id,
                Build.completed_at >= period_start,
                Build.completed_at < period_end,
                Build.status == "SUCCESS"
            ).count()
            values.append(self._create_value("build_success_rate", (success_builds / total_builds) * 100.0, team_id, period_start, period_end))
            
        # 8. Pipeline Duration (completion_time - start_time)
        build_records = self.db.query(Build).filter(
            Build.team_id == team_id,
            Build.completed_at >= period_start,
            Build.completed_at < period_end,
            Build.started_at != None
        ).all()
        if build_records:
            total_seconds = sum((b.completed_at - b.started_at).total_seconds() for b in build_records if b.completed_at and b.started_at)
            values.append(self._create_value("pipeline_duration", total_seconds / len(build_records), team_id, period_start, period_end))
            
        # 9. Deployment Failure Rate (failed_deployments / total_deployments)
        total_deps = self.db.query(Deployment).filter(
            Deployment.team_id == team_id,
            Deployment.completed_at >= period_start,
            Deployment.completed_at < period_end
        ).count()
        if total_deps > 0:
            failed_deps = self.db.query(Deployment).filter(
                Deployment.team_id == team_id,
                Deployment.completed_at >= period_start,
                Deployment.completed_at < period_end,
                Deployment.status == "FAILURE"
            ).count()
            values.append(self._create_value("deployment_failure_rate", (failed_deps / total_deps) * 100.0, team_id, period_start, period_end))
            
        # 10. Change Failure Rate (failed_changes / total_changes)
        # Failed changes can be deployments that result in incidents, or deployments that fail.
        # Typically it's deployments that fail or cause incidents.
        # For simplicity based on Plan: failed_changes / total_changes
        # total_changes = successful deployments in period
        if deployments > 0:
            # Check how many incidents occurred linked to these deployments, or just incidents in period for team?
            # A common definition is incidents divided by deployments.
            incidents_in_period = self.db.query(Incident).filter(
                Incident.team_id == team_id,
                Incident.created_at >= period_start,
                Incident.created_at < period_end
            ).count()
            cfr = (incidents_in_period / deployments) * 100.0
            values.append(self._create_value("change_failure_rate", cfr, team_id, period_start, period_end))

        # 11. MTTR (incident_resolution - incident_start)
        inc_records = self.db.query(Incident).filter(
            Incident.team_id == team_id,
            Incident.resolved_at >= period_start,
            Incident.resolved_at < period_end,
            Incident.created_at != None
        ).all()
        if inc_records:
            total_seconds = sum((i.resolved_at - i.created_at).total_seconds() for i in inc_records if i.resolved_at and i.created_at)
            values.append(self._create_value("mttr", total_seconds / len(inc_records), team_id, period_start, period_end))
            
        # 12. Work-in-Progress (active in-flight work in period)
        wip_count = self.db.query(WorkItem).filter(
            WorkItem.team_id == team_id,
            WorkItem.started_at < period_end,
            or_(WorkItem.completed_at == None, WorkItem.completed_at >= period_end)
        ).count()
        values.append(self._create_value("work_in_progress", float(wip_count), team_id, period_start, period_end))
        
        # Calculate baselines & percentage changes
        self._calculate_baselines_and_changes(values, team_id, period_start, period_end)
        
        for v in values:
            self.db.add(v)
        self.db.commit()
        
        return values

    def _create_value(self, metric_key: str, value: float, team_id: uuid.UUID, period_start: datetime, period_end: datetime) -> MetricValue:
        team = self.db.query(Team).get(team_id)
        
        return MetricValue(
            id=uuid.uuid4(),
            metric_id=self.metric_defs[metric_key].id,
            organization_id=team.organization_id if team else None,
            team_id=team_id,
            period_start=period_start,
            period_end=period_end,
            value=value
        )
        
    def _calculate_baselines_and_changes(self, current_values: list[MetricValue], team_id: uuid.UUID, current_start: datetime, current_end: datetime):
        duration = current_end - current_start
        prev_start = current_start - duration
        prev_end = current_start
        
        for val in current_values:
            prev_val = self.db.query(MetricValue).filter(
                MetricValue.metric_id == val.metric_id,
                MetricValue.team_id == team_id,
                MetricValue.period_start == prev_start,
                MetricValue.period_end == prev_end
            ).first()
            
            if prev_val:
                val.baseline_value = prev_val.value
                if prev_val.value != 0:
                    val.change_percentage = ((val.value - prev_val.value) / prev_val.value) * 100.0
                elif val.value > 0:
                    val.change_percentage = 100.0
                else:
                    val.change_percentage = 0.0

