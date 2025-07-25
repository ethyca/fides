"""add manual task tables

Revision ID: 5efcdf18438e
Revises: c586a56c25e7
Create Date: 2025-06-04 17:24:00.300170

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = "5efcdf18438e"
down_revision = "c586a56c25e7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "manual_task",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column(
            "task_type", sa.String(), nullable=False, server_default="privacy_request"
        ),
        sa.Column("parent_entity_id", sa.String(), nullable=False),
        sa.Column("parent_entity_type", sa.String(), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_entity_id",
            "parent_entity_type",
            name="uq_manual_task_parent_entity",
        ),
    )

    op.create_table(
        "manual_task_reference",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=False),
        sa.Column("reference_type", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["manual_task.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "manual_task_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("config_id", sa.String(), nullable=True),
        sa.Column("instance_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["manual_task.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for manual_task
    op.create_index("ix_manual_task_task_type", "manual_task", ["task_type"])
    op.create_index(
        "ix_manual_task_parent_entity",
        "manual_task",
        ["parent_entity_type", "parent_entity_id"],
    )
    op.create_index("ix_manual_task_due_date", "manual_task", ["due_date"])

    # Create indexes for manual_task_reference
    op.create_index(
        "ix_manual_task_reference_task_id", "manual_task_reference", ["task_id"]
    )
    op.create_index(
        "ix_manual_task_reference_reference",
        "manual_task_reference",
        ["reference_id", "reference_type"],
    )

    # Create indexes for manual_task_log
    op.create_index("ix_manual_task_log_task_id", "manual_task_log", ["task_id"])
    op.create_index("ix_manual_task_log_config_id", "manual_task_log", ["config_id"])
    op.create_index(
        "ix_manual_task_log_instance_id", "manual_task_log", ["instance_id"]
    )
    op.create_index("ix_manual_task_log_status", "manual_task_log", ["status"])
    op.create_index("ix_manual_task_log_created_at", "manual_task_log", ["created_at"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Drop indexes first
    op.drop_index("ix_manual_task_log_created_at", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_status", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_instance_id", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_config_id", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_task_id", table_name="manual_task_log")
    op.drop_index(
        "ix_manual_task_reference_reference", table_name="manual_task_reference"
    )
    op.drop_index(
        "ix_manual_task_reference_task_id", table_name="manual_task_reference"
    )
    op.drop_index("ix_manual_task_due_date", table_name="manual_task")
    op.drop_index("ix_manual_task_parent_entity", table_name="manual_task")
    op.drop_index("ix_manual_task_task_type", table_name="manual_task")

    # Then drop tables
    op.drop_table("manual_task_log")
    op.drop_table("manual_task_reference")
    op.drop_table("manual_task")
    # ### end Alembic commands ###
