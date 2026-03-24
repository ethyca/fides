"""add dashboard_snapshot table

Revision ID: 29113e44faec
Revises: 94273d7e8319
Create Date: 2026-03-24 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "29113e44faec"
down_revision = "94273d7e8319"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dashboardsnapshot",
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
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("metric_key", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_date",
            "metric_key",
            name="uq_dashboard_snapshot_date_metric",
        ),
    )
    op.create_index(
        "ix_dashboardsnapshot_snapshot_date",
        "dashboardsnapshot",
        ["snapshot_date"],
    )
    op.create_index(
        "ix_dashboardsnapshot_metric_key",
        "dashboardsnapshot",
        ["metric_key"],
    )


def downgrade():
    op.drop_index("ix_dashboardsnapshot_metric_key", table_name="dashboardsnapshot")
    op.drop_index("ix_dashboardsnapshot_snapshot_date", table_name="dashboardsnapshot")
    op.drop_table("dashboardsnapshot")
