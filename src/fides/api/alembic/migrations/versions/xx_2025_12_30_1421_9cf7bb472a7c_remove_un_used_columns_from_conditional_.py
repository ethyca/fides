"""remove unused columns from conditional dependencies

Revision ID: 9cf7bb472a7c
Revises: 85ce2c1c9579
Create Date: 2025-12-30 14:21:46.184655

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9cf7bb472a7c"
down_revision = "85ce2c1c9579"
branch_labels = None
depends_on = None


def upgrade():
    # === digest_condition table ===
    # Delete child rows (non-root) - their data is now in the root's condition_tree JSONB
    op.execute("DELETE FROM digest_condition WHERE parent_id IS NOT NULL")

    # Drop indexes on columns being removed
    op.drop_index("ix_digest_condition_condition_type", table_name="digest_condition")
    op.drop_index("ix_digest_condition_parent_id", table_name="digest_condition")
    op.drop_index("ix_digest_condition_sort_order", table_name="digest_condition")

    # Replace partial unique index with a full unique constraint
    op.drop_index(
        "ix_digest_condition_unique_root_per_type", table_name="digest_condition"
    )
    op.create_unique_constraint(
        "uq_digest_condition_config_type",
        "digest_condition",
        ["digest_config_id", "digest_condition_type"],
    )

    # Drop parent_id foreign key constraint and column
    op.drop_constraint(
        "digest_condition_parent_id_fkey", "digest_condition", type_="foreignkey"
    )
    op.drop_column("digest_condition", "parent_id")

    # Drop remaining unused columns
    op.drop_column("digest_condition", "sort_order")
    op.drop_column("digest_condition", "condition_type")
    op.drop_column("digest_condition", "operator")
    op.drop_column("digest_condition", "logical_operator")
    op.drop_column("digest_condition", "value")
    op.drop_column("digest_condition", "field_address")

    # === manual_task_conditional_dependency table ===
    # Delete child rows (non-root) - their data is now in the root's condition_tree JSONB
    op.execute(
        "DELETE FROM manual_task_conditional_dependency WHERE parent_id IS NOT NULL"
    )

    # Drop indexes on columns being removed
    op.drop_index(
        "ix_manual_task_conditional_dependency_condition_type",
        table_name="manual_task_conditional_dependency",
    )
    op.drop_index(
        "ix_manual_task_conditional_dependency_parent_id",
        table_name="manual_task_conditional_dependency",
    )
    op.drop_index(
        "ix_manual_task_conditional_dependency_sort_order",
        table_name="manual_task_conditional_dependency",
    )

    # Change manual_task_id index to unique and add unique constraint
    op.drop_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        table_name="manual_task_conditional_dependency",
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        "manual_task_conditional_dependency",
        ["manual_task_id"],
        unique=True,
    )
    op.create_unique_constraint(
        "uq_manual_task_conditional_dependency",
        "manual_task_conditional_dependency",
        ["manual_task_id"],
    )

    # Drop parent_id foreign key constraint and column
    op.drop_constraint(
        "manual_task_conditional_dependency_parent_id_fkey",
        "manual_task_conditional_dependency",
        type_="foreignkey",
    )
    op.drop_column("manual_task_conditional_dependency", "parent_id")

    # Drop remaining unused columns
    op.drop_column("manual_task_conditional_dependency", "sort_order")
    op.drop_column("manual_task_conditional_dependency", "condition_type")
    op.drop_column("manual_task_conditional_dependency", "operator")
    op.drop_column("manual_task_conditional_dependency", "logical_operator")
    op.drop_column("manual_task_conditional_dependency", "value")
    op.drop_column("manual_task_conditional_dependency", "field_address")


def downgrade():
    # NOTE: Child rows (parent_id IS NOT NULL) that were deleted during upgrade
    # cannot be recovered. Only the schema is restored, not the hierarchical data.
    # The condition_tree JSONB column still contains the full tree structure.

    # === manual_task_conditional_dependency table ===
    # Re-add columns
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("field_address", sa.VARCHAR(), nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("logical_operator", sa.VARCHAR(), nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("operator", sa.VARCHAR(), nullable=True),
    )
    # Add condition_type and sort_order as nullable first to handle existing rows
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("condition_type", sa.VARCHAR(), nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("sort_order", sa.INTEGER(), nullable=True),
    )
    # Set default values for existing root rows (root conditions are groups at position 0)
    op.execute(
        "UPDATE manual_task_conditional_dependency SET condition_type = 'group', sort_order = 0 WHERE condition_type IS NULL"
    )
    # Now make columns non-nullable
    op.alter_column(
        "manual_task_conditional_dependency",
        "condition_type",
        nullable=False,
    )
    op.alter_column(
        "manual_task_conditional_dependency",
        "sort_order",
        nullable=False,
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("parent_id", sa.VARCHAR(), nullable=True),
    )

    # Re-add parent_id foreign key
    op.create_foreign_key(
        "manual_task_conditional_dependency_parent_id_fkey",
        "manual_task_conditional_dependency",
        "manual_task_conditional_dependency",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Revert unique constraint and index changes
    op.drop_constraint(
        "uq_manual_task_conditional_dependency",
        "manual_task_conditional_dependency",
        type_="unique",
    )
    op.drop_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        table_name="manual_task_conditional_dependency",
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        "manual_task_conditional_dependency",
        ["manual_task_id"],
        unique=False,
    )

    # Re-add indexes
    op.create_index(
        "ix_manual_task_conditional_dependency_sort_order",
        "manual_task_conditional_dependency",
        ["sort_order"],
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_parent_id",
        "manual_task_conditional_dependency",
        ["parent_id"],
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_condition_type",
        "manual_task_conditional_dependency",
        ["condition_type"],
    )

    # === digest_condition table ===
    # Re-add columns
    op.add_column(
        "digest_condition",
        sa.Column("field_address", sa.VARCHAR(length=255), nullable=True),
    )
    op.add_column(
        "digest_condition",
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "digest_condition",
        sa.Column("logical_operator", sa.VARCHAR(), nullable=True),
    )
    op.add_column(
        "digest_condition",
        sa.Column("operator", sa.VARCHAR(), nullable=True),
    )
    # Add condition_type and sort_order as nullable first to handle existing rows
    op.add_column(
        "digest_condition",
        sa.Column("condition_type", sa.VARCHAR(), nullable=True),
    )
    op.add_column(
        "digest_condition",
        sa.Column("sort_order", sa.INTEGER(), nullable=True),
    )
    # Set default values for existing root rows (root conditions are groups at position 0)
    op.execute(
        "UPDATE digest_condition SET condition_type = 'group', sort_order = 0 WHERE condition_type IS NULL"
    )
    # Now make columns non-nullable
    op.alter_column(
        "digest_condition",
        "condition_type",
        nullable=False,
    )
    op.alter_column(
        "digest_condition",
        "sort_order",
        nullable=False,
    )
    op.add_column(
        "digest_condition",
        sa.Column("parent_id", sa.VARCHAR(length=255), nullable=True),
    )

    # Re-add parent_id foreign key
    op.create_foreign_key(
        "digest_condition_parent_id_fkey",
        "digest_condition",
        "digest_condition",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Revert unique constraint to partial index
    op.drop_constraint(
        "uq_digest_condition_config_type", "digest_condition", type_="unique"
    )
    op.create_index(
        "ix_digest_condition_unique_root_per_type",
        "digest_condition",
        ["digest_config_id", "digest_condition_type"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )

    # Re-add indexes
    op.create_index(
        "ix_digest_condition_sort_order", "digest_condition", ["sort_order"]
    )
    op.create_index("ix_digest_condition_parent_id", "digest_condition", ["parent_id"])
    op.create_index(
        "ix_digest_condition_condition_type",
        "digest_condition",
        ["condition_type"],
    )
