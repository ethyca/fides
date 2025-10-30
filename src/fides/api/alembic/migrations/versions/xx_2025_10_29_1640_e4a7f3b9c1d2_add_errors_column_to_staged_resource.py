"""Add errors column to staged resource table

Revision ID: e4a7f3b9c1d2
Revises: 5093e92e2a5a
Create Date: 2025-10-29 16:40:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e4a7f3b9c1d2"
down_revision = "67f0f2f4748e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stagedresource",
        sa.Column("errors", postgresql.JSONB(), nullable=True, server_default="{}"),
    )


def downgrade():
    op.drop_column("stagedresource", "errors")
