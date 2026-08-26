"""add ml_feature_vectors

Revision ID: phase11_ml_features
Revises: bb96b5547f1e
Create Date: 2026-08-26 20:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'phase11_ml_features'
down_revision: str | None = 'bb96b5547f1e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # Create ml_feature_vectors table
    op.create_table(
        'ml_feature_vectors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['core.organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['core.teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='analytics'
    )
    
    op.create_index(
        'idx_ml_feature_vectors_org_team_period',
        'ml_feature_vectors',
        ['organization_id', 'team_id', 'period_start', 'period_end'],
        unique=False,
        schema='analytics'
    )

def downgrade() -> None:
    op.drop_index('idx_ml_feature_vectors_org_team_period', table_name='ml_feature_vectors', schema='analytics')
    op.drop_table('ml_feature_vectors', schema='analytics')
