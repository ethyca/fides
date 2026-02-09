"""add config to manual task dependencies

Revision ID: 627c230d9917
Revises: 9cf7bb472a7c
Create Date: 2025-12-31 13:20:44.020508

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "627c230d9917"
down_revision = "9cf7bb472a7c"
branch_labels = None
depends_on = None


def upgrade():
    # Add config_field_key to manual_task_conditional_dependency
    # This stores the field_key string rather than the config_field_id UUID
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("config_field_key", sa.String(), nullable=True),
    )
    op.drop_constraint(
        "uq_manual_task_conditional_dependency",
        "manual_task_conditional_dependency",
        type_="unique",
    )
    op.drop_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        table_name="manual_task_conditional_dependency",
    )
    # Partial unique index for field-level conditions (when config_field_key IS NOT NULL)
    op.create_index(
        "ix_manual_task_cond_dep_task_field",
        "manual_task_conditional_dependency",
        ["manual_task_id", "config_field_key"],
        unique=True,
        postgresql_where=sa.text("config_field_key IS NOT NULL"),
    )
    # Partial unique index for task-level conditions (when config_field_key IS NULL)
    op.create_index(
        "ix_manual_task_cond_dep_task_only",
        "manual_task_conditional_dependency",
        ["manual_task_id"],
        unique=True,
        postgresql_where=sa.text("config_field_key IS NULL"),
    )
    op.create_index(
        op.f("ix_manual_task_conditional_dependency_config_field_key"),
        "manual_task_conditional_dependency",
        ["config_field_key"],
        unique=False,
    )

    # Add config_field_key to manual_task_reference
    op.add_column(
        "manual_task_reference",
        sa.Column("config_field_key", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_manual_task_reference_config_field_key",
        "manual_task_reference",
        ["config_field_key"],
        unique=False,
    )

    # Migrate config_type values from ManualTaskConfigurationType to ActionType
    op.execute(
        """
        UPDATE manual_task_config
        SET config_type = 'access'
        WHERE config_type = 'access_privacy_request'
    """
    )
    op.execute(
        """
        UPDATE manual_task_config
        SET config_type = 'erasure'
        WHERE config_type = 'erasure_privacy_request'
    """
    )

    # Add execution_timing to manual_task_config_field for field-level timing override
    op.add_column(
        "manual_task_config_field",
        sa.Column("execution_timing", sa.String(length=32), nullable=True),
    )


def downgrade():
    # Remove execution_timing from manual_task_config_field
    op.drop_column("manual_task_config_field", "execution_timing")
    # Revert config_type values from ActionType back to ManualTaskConfigurationType
    # Note: consent configs created after upgrade are converted to access_privacy_request
    # as there is no equivalent in the old ManualTaskConfigurationType enum
    op.execute(
        """
        UPDATE manual_task_config
        SET config_type = 'access_privacy_request'
        WHERE config_type IN ('access', 'consent')
    """
    )
    op.execute(
        """
        UPDATE manual_task_config
        SET config_type = 'erasure_privacy_request'
        WHERE config_type = 'erasure'
    """
    )

    # Remove config_field_key from manual_task_reference
    op.drop_index(
        "ix_manual_task_reference_config_field_key", table_name="manual_task_reference"
    )
    op.drop_column("manual_task_reference", "config_field_key")

    # Remove config_field_key from manual_task_conditional_dependency
    op.drop_index(
        op.f("ix_manual_task_conditional_dependency_config_field_key"),
        table_name="manual_task_conditional_dependency",
    )
    # Drop partial indexes
    op.execute(
        """
        DROP INDEX IF EXISTS ix_manual_task_cond_dep_task_field;
        DROP INDEX IF EXISTS ix_manual_task_cond_dep_task_only;
    """
    )
    # Delete field-level conditional dependencies before dropping config_field_key column.
    # The old schema only supports one task-level condition per manual_task_id, so we must
    # remove field-level conditions to avoid unique constraint violations.
    op.execute(
        """
        DELETE FROM manual_task_conditional_dependency
        WHERE config_field_key IS NOT NULL
    """
    )
    # Recreate the original basic index that was dropped in upgrade
    op.create_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        "manual_task_conditional_dependency",
        ["manual_task_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_manual_task_conditional_dependency",
        "manual_task_conditional_dependency",
        ["manual_task_id"],
    )
    op.drop_column("manual_task_conditional_dependency", "config_field_key")
