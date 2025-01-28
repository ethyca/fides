"""create table for persisting MonitorExecution records

Revision ID: ed96417b07d8
Revises: d9237a0c0d5a
Create Date: 2025-01-27 23:41:59.803285

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ed96417b07d8"
down_revision = "d9237a0c0d5a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "monitorexecution",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("monitor_config_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("started", sa.DateTime(), nullable=True),
        sa.Column("completed", sa.DateTime(), nullable=True),
        sa.Column(
            "classification_instances",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            default=[],
        ),
        sa.ForeignKeyConstraint(["monitor_config_key"], ["monitorconfig.key"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("monitorexecution")
