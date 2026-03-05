"""add jsonb tree column

Revision ID: 85ce2c1c9579
Revises: b9c8e7f6d5a4
Create Date: 2025-12-16 16:30:52.073758

"""

import json
from typing import Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.sql import quoted_name

# revision identifiers, used by Alembic.
revision = "85ce2c1c9579"
down_revision = "b9c8e7f6d5a4"
branch_labels = None
depends_on = None

# Whitelist of allowed table names for this migration
ALLOWED_TABLES = frozenset({"manual_task_conditional_dependency", "digest_condition"})
ALLOWED_ID_COLUMNS = frozenset({"id"})


def _validate_identifier(identifier: str, allowed: frozenset, identifier_type: str) -> str:
    """Validate that an identifier is in the allowed whitelist.

    Args:
        identifier: The table or column name to validate
        allowed: Set of allowed identifier values
        identifier_type: Description of the identifier type for error messages

    Returns:
        The validated identifier

    Raises:
        ValueError: If the identifier is not in the allowed set
    """
    if identifier not in allowed:
        raise ValueError(
            f"Invalid {identifier_type}: {identifier!r}. "
            f"Allowed values: {sorted(allowed)}"
        )
    return identifier


def _safe_identifier(name: str) -> quoted_name:
    """Return a properly quoted SQL identifier."""
    return quoted_name(name, quote=True)


def build_condition_tree(
    db: Session, table_name: str, row_id: str, id_column: str = "id"
) -> Optional[dict]:
    """Recursively build a condition tree from row-based storage.

    Args:
        db: Database session
        table_name: Name of the table (must be in ALLOWED_TABLES whitelist)
        row_id: ID of the row to build tree from
        id_column: Name of the ID column (must be in ALLOWED_ID_COLUMNS whitelist)

    Returns:
        dict: Condition tree as a dictionary (ConditionLeaf or ConditionGroup format)

    Raises:
        ValueError: If table_name or id_column is not in the allowed whitelist
    """
    # Validate identifiers against whitelist to prevent SQL injection
    _validate_identifier(table_name, ALLOWED_TABLES, "table name")
    _validate_identifier(id_column, ALLOWED_ID_COLUMNS, "id column")

    # Use quoted identifiers for defense in depth
    safe_table = _safe_identifier(table_name)
    safe_id_col = _safe_identifier(id_column)

    result = db.execute(
        sa.text(
            f"SELECT condition_type, field_address, operator, value, logical_operator "
            f"FROM {safe_table} WHERE {safe_id_col} = :row_id"
        ),
        {"row_id": row_id},
    ).fetchone()

    if not result:
        return None

    condition_type, field_address, operator, value, logical_operator = result

    if condition_type == "leaf":
        parsed_value = value

        return {
            "field_address": field_address,
            "operator": operator,
            "value": parsed_value,
        }

    # It's a group - get children ordered by sort_order
    children_rows = db.execute(
        sa.text(
            f"SELECT {safe_id_col} FROM {safe_table} "
            f"WHERE parent_id = :parent_id ORDER BY sort_order"
        ),
        {"parent_id": row_id},
    ).fetchall()

    child_conditions = []
    for (child_id,) in children_rows:
        child_tree = build_condition_tree(db, table_name, child_id, id_column)
        if child_tree:
            child_conditions.append(child_tree)

    if not child_conditions:
        return None

    return {
        "logical_operator": logical_operator,
        "conditions": child_conditions,
    }


def migrate_conditions(db: Session, table_name: str) -> None:
    """Migrate existing row-based condition trees to JSONB format for the given table.

    Args:
        db: Database session
        table_name: Name of the table (must be in ALLOWED_TABLES whitelist)

    Raises:
        ValueError: If table_name is not in the allowed whitelist
    """
    # Validate table name against whitelist
    _validate_identifier(table_name, ALLOWED_TABLES, "table name")
    safe_table = _safe_identifier(table_name)

    root_rows = db.execute(
        sa.text(f"SELECT id FROM {safe_table} WHERE parent_id IS NULL")
    ).fetchall()

    for (root_id,) in root_rows:
        tree = build_condition_tree(db, table_name, root_id)

        if tree:
            db.execute(
                sa.text(
                    f"UPDATE {safe_table} "
                    "SET condition_tree = :tree WHERE id = :root_id"
                ),
                {"tree": json.dumps(tree), "root_id": root_id},
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
    db = Session(op.get_bind())
    migrate_conditions(db, "manual_task_conditional_dependency")
    migrate_conditions(db, "digest_condition")
    db.commit()


def downgrade():
    op.drop_column("manual_task_conditional_dependency", "condition_tree")
    op.drop_column("digest_condition", "condition_tree")
