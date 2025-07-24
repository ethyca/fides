"""create table for persisting MonitorExecution records

Revision ID: ed96417b07d8
Revises: 1088e8353890
Create Date: 2025-01-27 23:41:59.803285

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ed96417b07d8"
down_revision = "1088e8353890"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "monitorexecution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("monitor_config_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("started", sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column("completed", sa.DateTime(), nullable=True),
        sa.Column(
            "classification_instances",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            default=[],
        ),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_monitorexecution_monitor_config_key",
        "monitorexecution",
        ["monitor_config_key"],
    )


def downgrade():
    op.drop_table("monitorexecution")
    op.drop_index(
        "ix_monitorexecution_monitor_config_key", table_name="monitorexecution"
    )
