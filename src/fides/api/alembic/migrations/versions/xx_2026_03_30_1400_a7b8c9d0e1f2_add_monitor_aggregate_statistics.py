"""add monitor_aggregate_statistics table

Revision ID: a7b8c9d0e1f2
Revises: c2d98bc00eeb
Create Date: 2026-03-30 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "c2d98bc00eeb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "monitor_aggregate_statistics",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("monitor_config_key", sa.String(), nullable=False),
        sa.Column("monitor_type", sa.String(length=50), nullable=False),
        sa.Column(
            "statistics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["monitor_config_key"],
            ["monitorconfig.key"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "monitor_config_key",
            name="uq_monitor_agg_stats_monitor_config_key",
        ),
    )
    op.create_index(
        "ix_monitor_aggregate_statistics_id",
        "monitor_aggregate_statistics",
        ["id"],
    )
    op.create_index(
        "ix_monitor_aggregate_statistics_monitor_type",
        "monitor_aggregate_statistics",
        ["monitor_type"],
    )


def downgrade():
    op.drop_index(
        "ix_monitor_aggregate_statistics_monitor_type",
        table_name="monitor_aggregate_statistics",
    )
    op.drop_index(
        "ix_monitor_aggregate_statistics_id",
        table_name="monitor_aggregate_statistics",
    )
    op.drop_table("monitor_aggregate_statistics")
