"""add model registry

Revision ID: phase12_model_registry
Revises: phase11_ml_features
Create Date: 2026-08-26 21:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'phase12_model_registry'
down_revision: str | None = 'phase11_ml_features'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # Create model_registry table
    op.create_table(
        'model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['core.organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['core.teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='configuration'
    )

def downgrade() -> None:
    op.drop_table('model_registry', schema='configuration')
