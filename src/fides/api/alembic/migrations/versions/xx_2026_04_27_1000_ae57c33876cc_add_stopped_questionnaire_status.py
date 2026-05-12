"""rename abandoned to stopped and make answer_version.created_by nullable

Revision ID: ae57c33876cc
Revises: d71c7d274c04
Create Date: 2026-04-27 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae57c33876cc"
down_revision = "d71c7d274c04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE questionnairestatus RENAME VALUE 'abandoned' TO 'stopped'")

    op.alter_column(
        "answer_version",
        "created_by",
        existing_type=sa.String(),
        nullable=True,
    )
    op.execute(
        "UPDATE answer_version SET created_by = NULL "
        "WHERE created_by IN ('system', 'scheduler', 'unknown')"
    )
    op.execute(
        "UPDATE answer_version av "
        "SET created_by = fu.email_address "
        "FROM fidesuser fu "
        "WHERE av.created_by = fu.username "
        "AND fu.email_address IS NOT NULL "
        "AND av.created_by NOT LIKE '%%@%%'"
    )


def downgrade():
    op.execute(
        "UPDATE answer_version SET created_by = 'system' WHERE created_by IS NULL"
    )
    op.alter_column(
        "answer_version",
        "created_by",
        existing_type=sa.String(),
        nullable=False,
    )
    op.execute("ALTER TYPE questionnairestatus RENAME VALUE 'stopped' TO 'abandoned'")
