import uuid
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.models.base import Base

class ProviderEvent(Base):
    __tablename__ = "provider_events"
    __table_args__ = (
        UniqueConstraint("provider", "external_event_id", name="uq_raw_provider_events_provider_external_id"),
        Index("idx_raw_events_timestamp", "event_timestamp"),
        Index("idx_raw_events_provider", "provider"),
        Index("idx_raw_events_received_at", "received_at"),
        Index("idx_raw_events_status", "processing_status"),
        {"schema": "raw"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(100), nullable=False)
    external_event_id = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    event_timestamp = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSONB, nullable=False)
    payload_hash = Column(String(128), nullable=True)
    source = Column(String(50), nullable=False)
    processing_status = Column(String(50), nullable=False, server_default="PENDING")
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
