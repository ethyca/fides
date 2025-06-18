"""add_manual_task_instance_table

Revision ID: 6a76a1fa4f3f
Revises: ba414a58ba90
Create Date: 2025-06-10 22:45:27.591492

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "6a76a1fa4f3f"
down_revision = "ba414a58ba90"
branch_labels = None
depends_on = None


def upgrade():
    # Add execution_timing column to manual_task_config
    op.add_column(
        "manual_task_config",
        sa.Column(
            "execution_timing",
            sa.String(),
            nullable=False,
            server_default="pre_execution",
        ),
    )

    # Remove due_date column from manual_task
    op.drop_column("manual_task", "due_date")

    # Create manual_task_instance table
    op.create_table(
        "manual_task_instance",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("config_id", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["config_id"], ["manual_task_config.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["task_id"], ["manual_task.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for manual_task_instance
    op.create_index(
        "ix_manual_task_instance_task_id", "manual_task_instance", ["task_id"]
    )
    op.create_index(
        "ix_manual_task_instance_config_id", "manual_task_instance", ["config_id"]
    )
    op.create_index(
        "ix_manual_task_instance_entity_id", "manual_task_instance", ["entity_id"]
    )
    op.create_index(
        "ix_manual_task_instance_entity_type", "manual_task_instance", ["entity_type"]
    )
    op.create_index(
        "ix_manual_task_instance_status", "manual_task_instance", ["status"]
    )
    op.create_index(
        "ix_manual_task_instance_completed_at", "manual_task_instance", ["completed_at"]
    )
    # Composite index for common query pattern
    op.create_index(
        "ix_manual_task_instance_entity",
        "manual_task_instance",
        ["entity_type", "entity_id"],
    )

    # Create manual_task_submission table
    op.create_table(
        "manual_task_submission",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("config_id", sa.String(), nullable=False),
        sa.Column("field_id", sa.String(), nullable=False),
        sa.Column("instance_id", sa.String(), nullable=False),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", JSONB, nullable=False),
        sa.ForeignKeyConstraint(
            ["config_id"], ["manual_task_config.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["field_id"], ["manual_task_config_field.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["instance_id"], ["manual_task_instance.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["task_id"], ["manual_task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["submitted_by"], ["fidesuser.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for manual_task_submission
    op.create_index(
        "ix_manual_task_submission_task_id", "manual_task_submission", ["task_id"]
    )
    op.create_index(
        "ix_manual_task_submission_config_id", "manual_task_submission", ["config_id"]
    )
    op.create_index(
        "ix_manual_task_submission_field_id", "manual_task_submission", ["field_id"]
    )
    op.create_index(
        "ix_manual_task_submission_instance_id",
        "manual_task_submission",
        ["instance_id"],
    )
    op.create_index(
        "ix_manual_task_submission_submitted_by",
        "manual_task_submission",
        ["submitted_by"],
    )
    op.create_index(
        "ix_manual_task_submission_submitted_at",
        "manual_task_submission",
        ["submitted_at"],
    )
    # Composite index for common query pattern
    op.create_index(
        "ix_manual_task_submission_instance_field",
        "manual_task_submission",
        ["instance_id", "field_id"],
    )

    # Add foreign key constraint to manual_task_log.instance_id
    op.create_foreign_key(
        "fk_manual_task_log_instance_id",
        "manual_task_log",
        "manual_task_instance",
        ["instance_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Update foreign key constraint for manual_task_log.config_id to use CASCADE
    op.drop_constraint(
        "fk_manual_task_log_config_id", "manual_task_log", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_manual_task_log_config_id",
        "manual_task_log",
        "manual_task_config",
        ["config_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    # Drop execution_timing column from manual_task_config
    op.drop_column("manual_task_config", "execution_timing")

    # Add due_date column to manual_task
    op.add_column(
        "manual_task",
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
    )

    # Drop foreign key constraint from manual_task_log.instance_id
    op.drop_constraint(
        "fk_manual_task_log_instance_id", "manual_task_log", type_="foreignkey"
    )

    # Revert foreign key constraint for manual_task_log.config_id back to SET NULL
    op.drop_constraint(
        "fk_manual_task_log_config_id", "manual_task_log", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_manual_task_log_config_id",
        "manual_task_log",
        "manual_task_config",
        ["config_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Drop indexes first
    op.drop_index(
        "ix_manual_task_submission_instance_field", table_name="manual_task_submission"
    )
    op.drop_index(
        "ix_manual_task_submission_submitted_at", table_name="manual_task_submission"
    )
    op.drop_index(
        "ix_manual_task_submission_submitted_by", table_name="manual_task_submission"
    )
    op.drop_index(
        "ix_manual_task_submission_instance_id", table_name="manual_task_submission"
    )
    op.drop_index(
        "ix_manual_task_submission_field_id", table_name="manual_task_submission"
    )
    op.drop_index(
        "ix_manual_task_submission_config_id", table_name="manual_task_submission"
    )
    op.drop_index(
        "ix_manual_task_submission_task_id", table_name="manual_task_submission"
    )

    op.drop_index("ix_manual_task_instance_entity", table_name="manual_task_instance")
    op.drop_index(
        "ix_manual_task_instance_completed_at", table_name="manual_task_instance"
    )
    op.drop_index("ix_manual_task_instance_status", table_name="manual_task_instance")
    op.drop_index(
        "ix_manual_task_instance_entity_type", table_name="manual_task_instance"
    )
    op.drop_index(
        "ix_manual_task_instance_entity_id", table_name="manual_task_instance"
    )
    op.drop_index(
        "ix_manual_task_instance_config_id", table_name="manual_task_instance"
    )
    op.drop_index("ix_manual_task_instance_task_id", table_name="manual_task_instance")

    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table("manual_task_submission")
    op.drop_table("manual_task_instance")
