"""Add errors column to staged resource table

Revision ID: e4a7f3b9c1d2
Revises: 80d28dea3b6b
Create Date: 2025-11-03 16:40:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e4a7f3b9c1d2"
down_revision = "80d28dea3b6b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stagedresource",
        sa.Column(
            "errors",
            postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade():
    op.drop_column("stagedresource", "errors")
