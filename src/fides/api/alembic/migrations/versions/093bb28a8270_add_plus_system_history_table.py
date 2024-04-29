"""Add plus_system_history table

Revision ID: 093bb28a8270
Revises: 3038667ba898
Create Date: 2023-08-18 23:48:22.934916

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "093bb28a8270"
down_revision = "3038667ba898"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_system_history",
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
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("system_id", sa.String(), nullable=False),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["ctl_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plus_system_history_id"), "plus_system_history", ["id"], unique=False
    )
    op.create_index(
        "idx_plus_system_history_created_at_system_id",
        "plus_system_history",
        ["created_at", "system_id"],
    )
    op.add_column(
        "ctl_systems",
        sa.Column("user_id", sa.String, nullable=True),
    )


def downgrade():
    op.drop_column("ctl_systems", "user_id")
    op.drop_index(
        op.f("idx_plus_system_history_created_at_system_id"),
        table_name="plus_system_history",
    )
    op.drop_index(op.f("ix_plus_system_history_id"), table_name="plus_system_history")
    op.drop_table("plus_system_history")
