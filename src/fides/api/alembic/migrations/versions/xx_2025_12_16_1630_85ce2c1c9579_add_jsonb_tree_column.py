"""add jsonb tree column

Revision ID: 85ce2c1c9579
Revises: b9c8e7f6d5a4
Create Date: 2025-12-16 16:30:52.073758

"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = "85ce2c1c9579"
down_revision = "b9c8e7f6d5a4"
branch_labels = None
depends_on = None


def build_condition_tree(
    db: Session, table_name: str, row_id: str, id_column: str = "id"
):
    """Recursively build a condition tree from row-based storage.

    Returns:
        dict: Condition tree as a dictionary (ConditionLeaf or ConditionGroup format)
    """
    result = db.execute(
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
            f"SELECT {id_column} FROM {table_name} "
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


def migrate_conditions(db: Session, table_name: str):
    """Migrate existing row-based condition trees to JSONB format for the given table."""
    root_rows = db.execute(
        sa.text(f"SELECT id FROM {table_name} WHERE parent_id IS NULL")
    ).fetchall()

    for (root_id,) in root_rows:
        tree = build_condition_tree(db, table_name, root_id)

        if tree:
            db.execute(
                sa.text(
                    f"UPDATE {table_name} "
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
