import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.models.base import Base

class MetricDefinition(Base):
    __tablename__ = "metric_definitions"
    __table_args__ = {"schema": "analytics"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    aggregation_method = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class MetricValue(Base):
    __tablename__ = "metric_values"
    __table_args__ = (
        Index("idx_metric_values_org_team_project_period", "organization_id", "team_id", "project_id", "period_start", "period_end"),
        {"schema": "analytics"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("analytics.metric_definitions.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("core.repositories.id", ondelete="SET NULL"), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    value = Column(Float, nullable=False)
    baseline_value = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)
    dimensions = Column(JSONB, nullable=False, server_default="{}")
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class HealthScore(Base):
    __tablename__ = "health_scores"
    __table_args__ = (
        Index("idx_health_scores_org_team_project_period", "organization_id", "team_id", "project_id", "period_start", "period_end"),
        {"schema": "analytics"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    score = Column(Float, nullable=False)
    previous_score = Column(Float, nullable=True)
    score_change = Column(Float, nullable=True)
    score_version = Column(String(50), nullable=False, server_default="v1.0")
    component_metrics = Column(JSONB, nullable=False, server_default="{}")
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class HealthScoreComponent(Base):
    __tablename__ = "health_score_components"
    __table_args__ = {"schema": "analytics"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    health_score_id = Column(UUID(as_uuid=True), ForeignKey("analytics.health_scores.id", ondelete="CASCADE"), nullable=False)
    dimension = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    contribution = Column(Float, nullable=False)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = {"schema": "analytics"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    metrics = Column(JSONB, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EngineeringTrend(Base):
    __tablename__ = "engineering_trends"
    __table_args__ = (
        Index("idx_engineering_trends_org_team_project_time", "organization_id", "team_id", "project_id", "detected_at"),
        {"schema": "analytics"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("analytics.metric_definitions.id", ondelete="CASCADE"), nullable=False)
    trend_type = Column(String(50), nullable=False)
    magnitude = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")


class Anomaly(Base):
    __tablename__ = "anomalies"
    __table_args__ = {"schema": "analytics"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("analytics.metric_definitions.id", ondelete="CASCADE"), nullable=False)
    severity = Column(String(30), nullable=False)
    baseline_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=False)
    change_percent = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    evidence = Column(JSONB, nullable=False, server_default="{}")
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Bottleneck(Base):
    __tablename__ = "bottlenecks"
    __table_args__ = {"schema": "analytics"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence = Column(JSONB, nullable=False, server_default="{}")
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIInsightRequest(Base):
    __tablename__ = "ai_insight_requests"
    __table_args__ = {"schema": "analytics"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"), nullable=True)
    model_provider = Column(String(100), nullable=False)
    model_name = Column(String(150), nullable=False)
    request_type = Column(String(100), nullable=False)
    sanitized_context = Column(JSONB, nullable=False)
    status = Column(String(30), nullable=False, server_default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class Insight(Base):
    __tablename__ = "insights"
    __table_args__ = {"schema": "analytics"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("analytics.ai_insight_requests.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="SET NULL"), nullable=True)
    insight_type = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)
    severity = Column(String(30), nullable=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    evidence = Column(JSONB, nullable=False, server_default="{}")
    source_metrics = Column(JSONB, nullable=False, server_default="{}")
    generated_by = Column(String(50), nullable=False, server_default="RULE_ENGINE")
    status = Column(String(30), nullable=False, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
