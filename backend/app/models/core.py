import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.models.base import Base

class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=True, unique=True)
    external_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(320), nullable=False, unique=True)
    display_name = Column(String(255), nullable=True)
    password_hash = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default="ACTIVE")
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "core"}

    user_id = Column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("core.roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"), nullable=True)


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    external_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = {"schema": "core"}

    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(50), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(100), nullable=True)
    name = Column(String(255), nullable=False)
    key = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    external_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = {"schema": "core"}

    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="CASCADE"), primary_key=True)
    access_level = Column(String(50), nullable=False, server_default="VIEWER")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_repositories_provider_external_id"),
        {"schema": "core"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    full_name = Column(String(500), nullable=True)
    url = Column(Text, nullable=True)
    default_branch = Column(String(255), nullable=True, server_default="main")
    language = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    status = Column(String(30), nullable=True, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class WorkItem(Base):
    __tablename__ = "work_items"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("core.repositories.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    item_type = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    status = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Change(Base):
    __tablename__ = "changes"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_changes_provider_external_id"),
        {"schema": "core"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("core.repositories.id", ondelete="CASCADE"), nullable=False)
    work_item_id = Column(UUID(as_uuid=True), ForeignKey("core.work_items.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    additions = Column(Integer, nullable=False, server_default="0", default=0)
    deletions = Column(Integer, nullable=False, server_default="0", default=0)
    changed_files = Column(Integer, nullable=False, server_default="0", default=0)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_id = Column(UUID(as_uuid=True), ForeignKey("core.changes.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=True)
    reviewer_reference = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Build(Base):
    __tablename__ = "builds"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_builds_provider_external_id"),
        {"schema": "core"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("core.repositories.id", ondelete="CASCADE"), nullable=False)
    change_id = Column(UUID(as_uuid=True), ForeignKey("core.changes.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    status = Column(String(50), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    branch = Column(String(255), nullable=True)
    commit_sha = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Deployment(Base):
    __tablename__ = "deployments"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_deployments_provider_external_id"),
        {"schema": "core"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("core.repositories.id", ondelete="SET NULL"), nullable=True)
    change_id = Column(UUID(as_uuid=True), ForeignKey("core.changes.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    environment = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    version = Column(String(255), nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("core.repositories.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    severity = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class CanonicalEvent(Base):
    __tablename__ = "canonical_events"
    __table_args__ = (
        Index("idx_canonical_events_org_team_project_time", "organization_id", "team_id", "project_id", "occurred_at"),
        Index("idx_canonical_events_repo_time", "repository_id", "occurred_at"),
        Index("idx_canonical_events_type_time", "event_type", "occurred_at"),
        {"schema": "core"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_event_id = Column(UUID(as_uuid=True), ForeignKey("raw.provider_events.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("core.repositories.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    actor_ref = Column(String(255), nullable=True)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(255), nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
