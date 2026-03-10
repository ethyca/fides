"""add monitor steward table

Revision ID: b9c8e7f6d5a4
Revises: dffb9da00fb1
Create Date: 2025-12-23 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b9c8e7f6d5a4"
down_revision = "dffb9da00fb1"
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
        sa.UniqueConstraint(
            "user_id", "monitor_config_id", name="uq_monitorsteward_user_monitor"
        ),
    )
    op.create_index(
        op.f("ix_monitorsteward_id"), "monitorsteward", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_monitorsteward_monitor_config_id"),
        "monitorsteward",
        ["monitor_config_id"],
        unique=False,
    )
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
