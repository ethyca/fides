"""add backfill history

Revision ID: 841e0b148993
Revises: a1b2c3d4e5f7
Create Date: 2026-02-03 20:29:57.879185

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "841e0b148993"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "backfill_history",
        sa.Column("backfill_name", sa.String(255), primary_key=True),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade():
    op.drop_table("backfill_history")
