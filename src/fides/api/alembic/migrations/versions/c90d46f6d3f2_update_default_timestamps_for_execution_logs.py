"""update default timestamps for execution logs

Revision ID: c90d46f6d3f2
Revises: abc53a00755b
Create Date: 2024-11-15 17:29:29.934671

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "c90d46f6d3f2"
down_revision = "abc53a00755b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "executionlog", "created_at", server_default=text("clock_timestamp()")
    )

    op.alter_column(
        "executionlog", "updated_at", server_default=text("clock_timestamp()")
    )


def downgrade():
    op.alter_column("executionlog", "created_at", server_default=text("now()"))

    op.alter_column("executionlog", "updated_at", server_default=text("now()"))
