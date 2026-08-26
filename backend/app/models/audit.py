import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_org_time", "organization_id", "created_at"),
        Index("idx_audit_logs_actor_time", "actor_user_id", "created_at"),
        {"schema": "audit"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="SET NULL"), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("core.users.id", ondelete="SET NULL"), nullable=True)
    actor_reference = Column(String(255), nullable=True)
    action = Column(String(150), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    previous_state = Column(JSONB, nullable=True)
    new_state = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DataProcessingJob(Base):
    __tablename__ = "data_processing_jobs"
    __table_args__ = {"schema": "audit"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(100), nullable=False)
    raw_event_id = Column(UUID(as_uuid=True), ForeignKey("raw.provider_events.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), nullable=False, server_default="PENDING")
    attempts = Column(Integer, nullable=False, server_default="0", default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
