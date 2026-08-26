import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.models.base import Base

class Provider(Base):
    __tablename__ = "providers"
    __table_args__ = {"schema": "configuration"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    provider_type = Column(String(50), nullable=False)
    version = Column(String(50), nullable=True)
    status = Column(String(30), nullable=False, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ConnectorConfig(Base):
    __tablename__ = "connector_configs"
    __table_args__ = {"schema": "configuration"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("configuration.providers.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    config = Column(JSONB, nullable=False, server_default="{}")
    is_enabled = Column(Boolean, nullable=False, server_default=text("true"))
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class HealthScoreConfig(Base):
    __tablename__ = "health_score_configs"
    __table_args__ = {"schema": "configuration"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    dimension = Column(String(100), nullable=False)
    weight = Column(Float, nullable=False)
    minimum_threshold = Column(Float, nullable=True)
    maximum_threshold = Column(Float, nullable=True)
    is_enabled = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class SystemSetting(Base):
    __tablename__ = "system_settings"
    __table_args__ = (
        UniqueConstraint("organization_id", "setting_key", name="uq_system_settings_org_setting_key"),
        {"schema": "configuration"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=False)
    setting_key = Column(String(150), nullable=False)
    setting_value = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    __table_args__ = {"schema": "configuration"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    file_path = Column(String(255), nullable=False)
    hyperparameters = Column(JSONB, nullable=False, server_default="{}")
    metrics = Column(JSONB, nullable=False, server_default="{}")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("core.organizations.id", ondelete="CASCADE"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("core.teams.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

