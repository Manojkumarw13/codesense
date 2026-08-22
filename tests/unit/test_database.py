import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from backend.app.core.database import SessionLocal, engine
from backend.app.models.base import Base
from backend.app.models.raw import ProviderEvent
from backend.app.models.core import (
    Organization,
    Team,
    Repository,
    Project,
    User,
    Role,
    Permission,
    UserRole,
    TeamMember,
    ProjectMember,
    WorkItem,
    Change,
    Review,
    Build,
    Deployment,
    Incident,
    CanonicalEvent,
)
from backend.app.models.analytics import (
    MetricDefinition,
    MetricValue,
    HealthScore,
    HealthScoreComponent,
    AnalyticsSnapshot,
    EngineeringTrend,
    Anomaly,
    Bottleneck,
    AIInsightRequest,
    Insight,
)
from backend.app.models.configuration import (
    Provider,
    ConnectorConfig,
    HealthScoreConfig,
    SystemSetting,
)
from backend.app.models.audit import (
    AuditLog,
    DataProcessingJob,
)


def test_all_schemas_exist():
    """Verify all 5 required PostgreSQL schemas exist in the database."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('raw', 'core', 'analytics', 'configuration', 'audit')")
        )
        schemas = {row[0] for row in result}
        assert schemas == {"raw", "core", "analytics", "configuration", "audit"}


def test_table_count_and_schemas():
    """Verify 34 tables are created across the 5 schemas."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('raw', 'core', 'analytics', 'configuration', 'audit')")
        )
        tables = {(row[0], row[1]) for row in result}
        assert len(tables) == 34


def test_no_forbidden_productivity_fields():
    """Verify non-negotiable rule: No individual productivity score columns exist."""
    forbidden = [
        "developer_productivity_score",
        "developer_performance_score",
        "developer_rank",
        "developer_efficiency_score",
        "individual_productivity_score",
    ]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_schema IN ('raw', 'core', 'analytics', 'configuration', 'audit')")
        )
        columns = [row[0] for row in result]
        for f in forbidden:
            assert f not in columns, f"Forbidden column {f} found in database schema!"


def test_crud_across_schemas():
    """Verify end-to-end insertion, querying, and relationships across all schemas."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1. Configuration Schema: Provider
        provider = Provider(
            name="github-test",
            provider_type="GIT",
            version="v3",
            status="ACTIVE",
        )
        db.add(provider)
        db.flush()

        # 2. Core Schema: Organization & Team
        org = Organization(
            name="Acme Corp",
            slug=f"acme-{uuid.uuid4().hex[:8]}",
            status="ACTIVE",
        )
        db.add(org)
        db.flush()

        team = Team(
            organization_id=org.id,
            name="Core Platform",
            status="ACTIVE",
        )
        db.add(team)
        db.flush()

        # 3. Core Schema: User & Roles
        user = User(
            organization_id=org.id,
            email=f"dev-{uuid.uuid4().hex[:8]}@acme.com",
            display_name="Jane Doe",
            status="ACTIVE",
        )
        role = Role(
            name=f"ADMIN_{uuid.uuid4().hex[:8]}",
            description="System Admin",
        )
        db.add_all([user, role])
        db.flush()

        user_role = UserRole(user_id=user.id, role_id=role.id)
        team_member = TeamMember(team_id=team.id, user_id=user.id, role="Lead")
        db.add_all([user_role, team_member])
        db.flush()

        # 4. Core Schema: Project & Repository
        project = Project(
            organization_id=org.id,
            team_id=team.id,
            name="Cloud Platform",
            key="CP",
        )
        db.add(project)
        db.flush()

        repo = Repository(
            team_id=team.id,
            project_id=project.id,
            provider="github",
            external_id=f"repo-{uuid.uuid4().hex[:8]}",
            name="core-service",
        )
        db.add(repo)
        db.flush()

        # 5. Raw Schema: ProviderEvent
        raw_event = ProviderEvent(
            provider="github",
            external_event_id=f"evt-{uuid.uuid4().hex[:8]}",
            event_type="pull_request.opened",
            payload={"action": "opened", "number": 42},
            source="webhook",
            processing_status="PROCESSED",
        )
        db.add(raw_event)
        db.flush()

        # 6. Core Schema: Change, Review, Build, Deployment, Incident, CanonicalEvent
        change = Change(
            team_id=team.id,
            repository_id=repo.id,
            provider="github",
            external_id=f"pr-{uuid.uuid4().hex[:8]}",
            title="Add feature X",
            status="MERGED",
        )
        db.add(change)
        db.flush()

        review = Review(
            change_id=change.id,
            provider="github",
            status="APPROVED",
        )
        build = Build(
            team_id=team.id,
            repository_id=repo.id,
            change_id=change.id,
            provider="github",
            external_id=f"build-{uuid.uuid4().hex[:8]}",
            status="SUCCESS",
            duration_seconds=120,
        )
        deployment = Deployment(
            team_id=team.id,
            repository_id=repo.id,
            change_id=change.id,
            provider="github",
            external_id=f"dep-{uuid.uuid4().hex[:8]}",
            environment="PRODUCTION",
            status="SUCCESS",
            duration_seconds=45,
        )
        incident = Incident(
            team_id=team.id,
            repository_id=repo.id,
            provider="github",
            external_id=f"inc-{uuid.uuid4().hex[:8]}",
            title="Service latency spike",
            severity="SEV2",
            status="RESOLVED",
        )
        canonical_event = CanonicalEvent(
            raw_event_id=raw_event.id,
            organization_id=org.id,
            team_id=team.id,
            project_id=project.id,
            repository_id=repo.id,
            event_type="CHANGE_CREATED",
            occurred_at=now,
            entity_type="change",
            entity_id=str(change.id),
        )
        db.add_all([review, build, deployment, incident, canonical_event])
        db.flush()

        # 7. Analytics Schema: MetricDefinition, MetricValue, HealthScore, Components
        metric_def = MetricDefinition(
            metric_key=f"cycle_time_{uuid.uuid4().hex[:8]}",
            name="Cycle Time",
            category="DELIVERY",
            unit="hours",
        )
        db.add(metric_def)
        db.flush()

        metric_val = MetricValue(
            metric_id=metric_def.id,
            team_id=team.id,
            period_start=now,
            period_end=now,
            value=24.5,
        )
        health_score = HealthScore(
            team_id=team.id,
            period_start=now,
            period_end=now,
            score=88.5,
            previous_score=85.0,
            score_change=3.5,
        )
        db.add_all([metric_val, health_score])
        db.flush()

        health_comp = HealthScoreComponent(
            health_score_id=health_score.id,
            dimension="delivery_flow",
            score=90.0,
            weight=0.20,
            contribution=18.0,
        )
        anomaly = Anomaly(
            team_id=team.id,
            metric_id=metric_def.id,
            severity="MEDIUM",
            observed_value=30.0,
            baseline_value=20.0,
        )
        bottleneck = Bottleneck(
            team_id=team.id,
            category="REVIEW",
            severity="HIGH",
            title="Review queue growing",
        )
        insight = Insight(
            organization_id=org.id,
            team_id=team.id,
            project_id=project.id,
            insight_type="BOTTLENECK_DETECTED",
            title="Review backlog detected",
            content="Turnaround time increased by 30%",
            status="ACTIVE",
        )
        db.add_all([health_comp, anomaly, bottleneck, insight])
        db.flush()

        # 8. Audit Schema: AuditLog, DataProcessingJob
        audit = AuditLog(
            organization_id=org.id,
            actor_user_id=user.id,
            action="TEAM_CREATED",
            resource_type="team",
            resource_id=team.id,
        )
        job = DataProcessingJob(
            job_type="EVENT_NORMALIZATION",
            raw_event_id=raw_event.id,
            status="COMPLETED",
        )
        db.add_all([audit, job])
        db.commit()

        # Verify query back
        retrieved_hs = db.query(HealthScore).filter_by(id=health_score.id).first()
        assert retrieved_hs is not None
        assert retrieved_hs.score == 88.5

        retrieved_raw = db.query(ProviderEvent).filter_by(id=raw_event.id).first()
        assert retrieved_raw is not None
        assert retrieved_raw.payload["number"] == 42

    finally:
        db.rollback()
        db.close()
