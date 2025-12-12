"""migrate to one row conditional dependency model and remove manual_task_log

Revision ID: c37e8fde5a71
Revises: a7241db3ee6a
Create Date: 2025-12-12 13:13:45.965985

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c37e8fde5a71"
down_revision = "a7241db3ee6a"
branch_labels = None
depends_on = None


def build_condition_tree(connection, table_name, row_id, id_column="id"):
    """Recursively build a condition tree from row-based storage.

    Args:
        connection: Database connection
        table_name: Name of the table to query
        row_id: ID of the current row
        id_column: Name of the ID column

    Returns:
        dict: Condition tree as a dictionary (ConditionLeaf or ConditionGroup format)
    """
    result = connection.execute(
        sa.text(
            f"SELECT condition_type, field_address, operator, value, logical_operator "
            f"FROM {table_name} WHERE {id_column} = :row_id"
        ),
        {"row_id": row_id},
    ).fetchone()

    if not result:
        return None

    condition_type, field_address, operator, value, logical_operator = result

    if condition_type == "leaf":
        # Parse value from JSONB if it's a string
        parsed_value = value
        if isinstance(value, str):
            try:
                parsed_value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                parsed_value = value

        return {
            "field_address": field_address,
            "operator": operator,
            "value": parsed_value,
        }

    # It's a group - get children ordered by sort_order
    children_rows = connection.execute(
        sa.text(
            f"SELECT {id_column} FROM {table_name} "
            f"WHERE parent_id = :parent_id ORDER BY sort_order"
        ),
        {"parent_id": row_id},
    ).fetchall()

    child_conditions = []
    for (child_id,) in children_rows:
        child_tree = build_condition_tree(connection, table_name, child_id, id_column)
        if child_tree:
            child_conditions.append(child_tree)

    if not child_conditions:
        return None

    return {
        "logical_operator": logical_operator,
        "conditions": child_conditions,
    }


def migrate_manual_task_conditions(connection):
    """Migrate manual_task_conditional_dependency rows to JSONB trees."""
    # Find all root conditions (parent_id IS NULL)
    root_rows = connection.execute(
        sa.text(
            "SELECT id, manual_task_id FROM manual_task_conditional_dependency "
            "WHERE parent_id IS NULL"
        )
    ).fetchall()

    for root_id, manual_task_id in root_rows:
        # Build the full tree
        tree = build_condition_tree(
            connection, "manual_task_conditional_dependency", root_id
        )

        if tree:
            # Update the root row with the full tree
            connection.execute(
                sa.text(
                    "UPDATE manual_task_conditional_dependency "
                    "SET condition_tree = :tree WHERE id = :root_id"
                ),
                {"tree": json.dumps(tree), "root_id": root_id},
            )

    # Delete all non-root rows (they're now stored in JSONB)
    connection.execute(
        sa.text(
            "DELETE FROM manual_task_conditional_dependency WHERE parent_id IS NOT NULL"
        )
    )


def migrate_digest_conditions(connection):
    """Migrate digest_condition rows to JSONB trees."""
    # Find all root conditions (parent_id IS NULL)
    root_rows = connection.execute(
        sa.text(
            "SELECT id, digest_config_id, digest_condition_type FROM digest_condition "
            "WHERE parent_id IS NULL"
        )
    ).fetchall()

    for root_id, digest_config_id, digest_condition_type in root_rows:
        # Build the full tree
        tree = build_condition_tree(connection, "digest_condition", root_id)

        if tree:
            # Update the root row with the full tree
            connection.execute(
                sa.text(
                    "UPDATE digest_condition "
                    "SET condition_tree = :tree WHERE id = :root_id"
                ),
                {"tree": json.dumps(tree), "root_id": root_id},
            )

    # Delete all non-root rows (they're now stored in JSONB)
    connection.execute(
        sa.text("DELETE FROM digest_condition WHERE parent_id IS NOT NULL")
    )


def upgrade():
    # Step 1: Add condition_tree column to both tables
    op.add_column(
        "digest_condition",
        sa.Column(
            "condition_tree", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column(
            "condition_tree", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # Step 2: Migrate existing row-based trees to JSONB
    connection = op.get_bind()
    migrate_manual_task_conditions(connection)
    migrate_digest_conditions(connection)

    # Step 3: Drop old columns and indexes for digest_condition
    op.drop_index("ix_digest_condition_condition_type", table_name="digest_condition")
    op.drop_index("ix_digest_condition_parent_id", table_name="digest_condition")
    op.drop_index("ix_digest_condition_sort_order", table_name="digest_condition")
    op.drop_index(
        "ix_digest_condition_unique_root_per_type", table_name="digest_condition"
    )
    op.create_unique_constraint(
        "uq_digest_condition_config_type",
        "digest_condition",
        ["digest_config_id", "digest_condition_type"],
    )
    op.drop_constraint(
        "digest_condition_parent_id_fkey", "digest_condition", type_="foreignkey"
    )
    op.drop_column("digest_condition", "condition_type")
    op.drop_column("digest_condition", "logical_operator")
    op.drop_column("digest_condition", "field_address")
    op.drop_column("digest_condition", "parent_id")
    op.drop_column("digest_condition", "sort_order")
    op.drop_column("digest_condition", "value")
    op.drop_column("digest_condition", "operator")

    # Step 4: Drop old columns and indexes for manual_task_conditional_dependency
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
    op.drop_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        table_name="manual_task_conditional_dependency",
    )
    op.create_index(
        op.f("ix_manual_task_conditional_dependency_manual_task_id"),
        "manual_task_conditional_dependency",
        ["manual_task_id"],
        unique=True,
    )
    op.drop_constraint(
        "manual_task_conditional_dependency_parent_id_fkey",
        "manual_task_conditional_dependency",
        type_="foreignkey",
    )
    op.drop_column("manual_task_conditional_dependency", "condition_type")
    op.drop_column("manual_task_conditional_dependency", "logical_operator")
    op.drop_column("manual_task_conditional_dependency", "field_address")
    op.drop_column("manual_task_conditional_dependency", "parent_id")
    op.drop_column("manual_task_conditional_dependency", "sort_order")
    op.drop_column("manual_task_conditional_dependency", "value")
    op.drop_column("manual_task_conditional_dependency", "operator")



def downgrade():
    # Note: Downgrade will lose the JSONB tree structure - data migration is one-way
    # Re-add columns for manual_task_conditional_dependency
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("operator", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column(
            "value",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column(
            "sort_order",
            sa.INTEGER(),
            autoincrement=False,
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("parent_id", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("field_address", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column("logical_operator", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "manual_task_conditional_dependency",
        sa.Column(
            "condition_type",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=False,
            server_default="leaf",
        ),
    )
    op.create_foreign_key(
        "manual_task_conditional_dependency_parent_id_fkey",
        "manual_task_conditional_dependency",
        "manual_task_conditional_dependency",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_index(
        op.f("ix_manual_task_conditional_dependency_manual_task_id"),
        table_name="manual_task_conditional_dependency",
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_manual_task_id",
        "manual_task_conditional_dependency",
        ["manual_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_sort_order",
        "manual_task_conditional_dependency",
        ["sort_order"],
        unique=False,
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_parent_id",
        "manual_task_conditional_dependency",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        "ix_manual_task_conditional_dependency_condition_type",
        "manual_task_conditional_dependency",
        ["condition_type"],
        unique=False,
    )
    op.drop_column("manual_task_conditional_dependency", "condition_tree")

    # Re-add columns for digest_condition
    op.add_column(
        "digest_condition",
        sa.Column("operator", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "digest_condition",
        sa.Column(
            "value",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "digest_condition",
        sa.Column(
            "sort_order",
            sa.INTEGER(),
            autoincrement=False,
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "digest_condition",
        sa.Column(
            "parent_id", sa.VARCHAR(length=255), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "digest_condition",
        sa.Column(
            "field_address", sa.VARCHAR(length=255), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "digest_condition",
        sa.Column("logical_operator", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "digest_condition",
        sa.Column(
            "condition_type",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=False,
            server_default="leaf",
        ),
    )
    op.create_foreign_key(
        "digest_condition_parent_id_fkey",
        "digest_condition",
        "digest_condition",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "uq_digest_condition_config_type", "digest_condition", type_="unique"
    )
    op.create_index(
        "ix_digest_condition_unique_root_per_type",
        "digest_condition",
        ["digest_config_id", "digest_condition_type"],
        unique=False,
    )
    op.create_index(
        "ix_digest_condition_sort_order",
        "digest_condition",
        ["sort_order"],
        unique=False,
    )
    op.create_index(
        "ix_digest_condition_parent_id", "digest_condition", ["parent_id"], unique=False
    )
    op.create_index(
        "ix_digest_condition_condition_type",
        "digest_condition",
        ["condition_type"],
        unique=False,
    )
    op.drop_column("digest_condition", "condition_tree")
