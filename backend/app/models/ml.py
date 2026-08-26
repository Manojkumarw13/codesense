import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.models.base import Base


class MLFeatureVector(Base):
    __tablename__ = "ml_feature_vectors"
    __table_args__ = (
        Index("idx_ml_feature_vectors_org_team_period", "organization_id", "team_id", "period_start", "period_end"),
        {"schema": "analytics"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=False)
    
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    features = Column(JSONB, nullable=False, server_default="{}")
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
