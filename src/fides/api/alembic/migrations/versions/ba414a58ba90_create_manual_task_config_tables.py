"""create manual task config tables

Revision ID: ba414a58ba90
Revises: 29e56fa1fdb3
Create Date: 2025-06-09 19:56:18.254209

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "ba414a58ba90"
down_revision = "29e56fa1fdb3"
branch_labels = None
depends_on = None


def upgrade():
    # Create manual_task_config table
    op.create_table(
        "manual_task_config",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("config_type", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["task_id"], ["manual_task.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create manual_task_config_field table
    op.create_table(
        "manual_task_config_field",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("config_id", sa.String(), nullable=False),
        sa.Column("field_key", sa.String(), nullable=False),
        sa.Column("field_type", sa.String(), nullable=False),
        sa.Column("field_metadata", JSONB, nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["task_id"], ["manual_task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["config_id"], ["manual_task_config.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "config_id", "field_key", name="unique_field_key_per_config"
        ),
    )

    # Add foreign key constraint to manual_task_log table
    op.create_foreign_key(
        "fk_manual_task_log_config_id",
        "manual_task_log",
        "manual_task_config",
        ["config_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create indexes
    op.create_index("ix_manual_task_config_task_id", "manual_task_config", ["task_id"])
    op.create_index(
        "ix_manual_task_config_config_type", "manual_task_config", ["config_type"]
    )
    op.create_index(
        "ix_manual_task_config_field_task_id", "manual_task_config_field", ["task_id"]
    )
    op.create_index(
        "ix_manual_task_config_field_config_id",
        "manual_task_config_field",
        ["config_id"],
    )
    op.create_index(
        "ix_manual_task_config_field_field_key",
        "manual_task_config_field",
        ["field_key"],
    )


def downgrade():
    # Drop indexes
    op.drop_index("ix_manual_task_config_field_field_key")
    op.drop_index("ix_manual_task_config_field_config_id")
    op.drop_index("ix_manual_task_config_field_task_id")
    op.drop_index("ix_manual_task_config_config_type")
    op.drop_index("ix_manual_task_config_task_id")

    # Drop foreign key constraint from manual_task_log
    op.drop_constraint(
        "fk_manual_task_log_config_id", "manual_task_log", type_="foreignkey"
    )

    # Drop tables
    op.drop_table("manual_task_config_field")
    op.drop_table("manual_task_config")
