"""Create cloud_infra_staged_resource table

Revision ID: 22cf8ccaec40
Revises: d4e5f6a7b8c9
Create Date: 2026-04-02 21:46:16.484694

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '22cf8ccaec40'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('cloud_infra_staged_resource',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('urn', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('monitor_config_id', sa.String(), nullable=True),
        sa.Column('diff_status', sa.String(), nullable=True),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('service', sa.String(), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('cloud_account_id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('monitor_config_id', 'source_id', name='uq_cloud_infra_monitor_config_id_source_id')
    )
    op.create_index(op.f('ix_cloud_infra_staged_resource_cloud_account_id'), 'cloud_infra_staged_resource', ['cloud_account_id'], unique=False)
    op.create_index(op.f('ix_cloud_infra_staged_resource_diff_status'), 'cloud_infra_staged_resource', ['diff_status'], unique=False)
    op.create_index(op.f('ix_cloud_infra_staged_resource_id'), 'cloud_infra_staged_resource', ['id'], unique=False)
    op.create_index(op.f('ix_cloud_infra_staged_resource_location'), 'cloud_infra_staged_resource', ['location'], unique=False)
    op.create_index(op.f('ix_cloud_infra_staged_resource_monitor_config_id'), 'cloud_infra_staged_resource', ['monitor_config_id'], unique=False)
    op.create_index(op.f('ix_cloud_infra_staged_resource_resource_type'), 'cloud_infra_staged_resource', ['resource_type'], unique=False)
    op.create_index(op.f('ix_cloud_infra_staged_resource_urn'), 'cloud_infra_staged_resource', ['urn'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_cloud_infra_staged_resource_urn'), table_name='cloud_infra_staged_resource')
    op.drop_index(op.f('ix_cloud_infra_staged_resource_resource_type'), table_name='cloud_infra_staged_resource')
    op.drop_index(op.f('ix_cloud_infra_staged_resource_monitor_config_id'), table_name='cloud_infra_staged_resource')
    op.drop_index(op.f('ix_cloud_infra_staged_resource_location'), table_name='cloud_infra_staged_resource')
    op.drop_index(op.f('ix_cloud_infra_staged_resource_id'), table_name='cloud_infra_staged_resource')
    op.drop_index(op.f('ix_cloud_infra_staged_resource_diff_status'), table_name='cloud_infra_staged_resource')
    op.drop_index(op.f('ix_cloud_infra_staged_resource_cloud_account_id'), table_name='cloud_infra_staged_resource')
    op.drop_constraint('uq_cloud_infra_monitor_config_id_source_id', 'cloud_infra_staged_resource', type_='unique')
    op.drop_table('cloud_infra_staged_resource')
