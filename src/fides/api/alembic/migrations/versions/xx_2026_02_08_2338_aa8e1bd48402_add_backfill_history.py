"""add backfill history

Revision ID: aa8e1bd48402
Revises: b2c3d4e5f6g7
Create Date: 2026-02-08 23:38:48.431833

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "aa8e1bd48402"
down_revision = "b2c3d4e5f6g7"
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
