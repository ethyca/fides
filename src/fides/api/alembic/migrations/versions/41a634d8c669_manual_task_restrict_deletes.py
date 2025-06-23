"""manual task allow deletion with orphaned configs

Revision ID: 41a634d8c669
Revises: aadfe83c5644
Create Date: 2025-06-22 19:34:22.336406

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "41a634d8c669"
down_revision = "aadfe83c5644"
branch_labels = None
depends_on = None


def upgrade():
    """Allow manual task deletion by making task_id nullable and using SET NULL constraints."""

    # Make task_id columns nullable to support orphaned records
    op.alter_column("manual_task_config", "task_id", nullable=True)
    op.alter_column("manual_task_instance", "task_id", nullable=True)
    op.alter_column("manual_task_submission", "task_id", nullable=True)
    op.alter_column("manual_task_config_field", "task_id", nullable=True)
    op.alter_column("manual_task_log", "task_id", nullable=True)

    # manual_task_config: Change task_id to SET NULL (preserve configs when task deleted)
    op.drop_constraint(
        "manual_task_config_task_id_fkey", "manual_task_config", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "manual_task_config",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # manual_task_instance: Change task_id to SET NULL (preserve instances when task deleted)
    # Keep config_id as RESTRICT (instances should not be deleted when config deleted)
    op.drop_constraint(
        "manual_task_instance_config_id_fkey",
        "manual_task_instance",
        type_="foreignkey",
    )
    op.drop_constraint(
        "manual_task_instance_task_id_fkey", "manual_task_instance", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "manual_task_instance",
        "manual_task_config",
        ["config_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        None,
        "manual_task_instance",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # manual_task_submission: Change task_id to SET NULL, keep others as RESTRICT
    # Keep instance_id as CASCADE since submissions should be deleted when instance is deleted
    op.drop_constraint(
        "manual_task_submission_config_id_fkey",
        "manual_task_submission",
        type_="foreignkey",
    )
    op.drop_constraint(
        "manual_task_submission_field_id_fkey",
        "manual_task_submission",
        type_="foreignkey",
    )
    op.drop_constraint(
        "manual_task_submission_task_id_fkey",
        "manual_task_submission",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None,
        "manual_task_submission",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        None,
        "manual_task_submission",
        "manual_task_config",
        ["config_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        None,
        "manual_task_submission",
        "manual_task_config_field",
        ["field_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # manual_task_config_field: Change task_id to SET NULL (preserve fields when task deleted)
    op.drop_constraint(
        "manual_task_config_field_task_id_fkey",
        "manual_task_config_field",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None,
        "manual_task_config_field",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # manual_task_log: Change task_id to SET NULL (preserve logs when task deleted)
    op.drop_constraint(
        "manual_task_log_task_id_fkey", "manual_task_log", type_="foreignkey"
    )
    op.create_foreign_key(
        "manual_task_log_task_id_fkey",
        "manual_task_log",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    """Revert to original CASCADE behavior and make task_id non-nullable."""

    # Revert manual_task_log constraints
    op.drop_constraint(
        "manual_task_log_task_id_fkey", "manual_task_log", type_="foreignkey"
    )
    op.create_foreign_key(
        "manual_task_log_task_id_fkey",
        "manual_task_log",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Revert manual_task_config_field constraints
    op.drop_constraint(
        "manual_task_config_field_task_id_fkey",
        "manual_task_config_field",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "manual_task_config_field_task_id_fkey",
        "manual_task_config_field",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Revert manual_task_submission constraints
    op.drop_constraint(
        "manual_task_submission_task_id_fkey",
        "manual_task_submission",
        type_="foreignkey",
    )
    op.drop_constraint(
        "manual_task_submission_field_id_fkey",
        "manual_task_submission",
        type_="foreignkey",
    )
    op.drop_constraint(
        "manual_task_submission_config_id_fkey",
        "manual_task_submission",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "manual_task_submission_task_id_fkey",
        "manual_task_submission",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "manual_task_submission_field_id_fkey",
        "manual_task_submission",
        "manual_task_config_field",
        ["field_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "manual_task_submission_config_id_fkey",
        "manual_task_submission",
        "manual_task_config",
        ["config_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Revert manual_task_instance constraints
    op.drop_constraint(
        "manual_task_instance_task_id_fkey", "manual_task_instance", type_="foreignkey"
    )
    op.drop_constraint(
        "manual_task_instance_config_id_fkey",
        "manual_task_instance",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "manual_task_instance_task_id_fkey",
        "manual_task_instance",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "manual_task_instance_config_id_fkey",
        "manual_task_instance",
        "manual_task_config",
        ["config_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Revert manual_task_config constraints
    op.drop_constraint(
        "manual_task_config_task_id_fkey", "manual_task_config", type_="foreignkey"
    )
    op.create_foreign_key(
        "manual_task_config_task_id_fkey",
        "manual_task_config",
        "manual_task",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Make task_id columns non-nullable again
    op.alter_column("manual_task_log", "task_id", nullable=False)
    op.alter_column("manual_task_config_field", "task_id", nullable=False)
    op.alter_column("manual_task_submission", "task_id", nullable=False)
    op.alter_column("manual_task_instance", "task_id", nullable=False)
    op.alter_column("manual_task_config", "task_id", nullable=False)
