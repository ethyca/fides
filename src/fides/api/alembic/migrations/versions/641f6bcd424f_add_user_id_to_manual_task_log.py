"""add user_id to manual_task_log

Revision ID: 641f6bcd424f
Revises: 41a634d8c669
Create Date: 2025-07-02 03:19:40.171201

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "641f6bcd424f"
down_revision = "41a634d8c669"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("manual_task_log", sa.Column("user_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_manual_task_log_user_id"), "manual_task_log", ["user_id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_manual_task_log_user_id"), table_name="manual_task_log")
    op.drop_column("manual_task_log", "user_id")
