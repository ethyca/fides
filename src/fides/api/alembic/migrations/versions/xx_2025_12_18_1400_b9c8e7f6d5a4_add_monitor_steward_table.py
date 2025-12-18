"""add monitor steward table

Revision ID: b9c8e7f6d5a4
Revises: f8a9b0c1d2e3
Create Date: 2025-12-18 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b9c8e7f6d5a4"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "monitorsteward",
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
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("monitor_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["monitor_config_id"], ["monitorconfig.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["fidesuser.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_monitorsteward_id"), "monitorsteward", ["id"], unique=False
    )
    # Index for efficient lookup of stewards by monitor (used by GET /{monitor_key}/stewards)
    op.create_index(
        op.f("ix_monitorsteward_monitor_config_id"),
        "monitorsteward",
        ["monitor_config_id"],
        unique=False,
    )
    # Index for efficient lookup of monitors by steward (used by steward filtering)
    op.create_index(
        op.f("ix_monitorsteward_user_id"),
        "monitorsteward",
        ["user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_monitorsteward_user_id"), table_name="monitorsteward")
    op.drop_index(
        op.f("ix_monitorsteward_monitor_config_id"), table_name="monitorsteward"
    )
    op.drop_index(op.f("ix_monitorsteward_id"), table_name="monitorsteward")
    op.drop_table("monitorsteward")
