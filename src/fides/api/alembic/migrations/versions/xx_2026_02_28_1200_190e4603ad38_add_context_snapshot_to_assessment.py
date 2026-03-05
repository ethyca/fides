"""Add context_snapshot and last_evaluated_at to privacy_assessment

Revision ID: 190e4603ad38
Revises: 074796d61d8a
Create Date: 2026-02-28 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "190e4603ad38"
down_revision = "074796d61d8a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacy_assessment",
        sa.Column(
            "context_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "privacy_assessment",
        sa.Column(
            "last_evaluated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("privacy_assessment", "last_evaluated_at")
    op.drop_column("privacy_assessment", "context_snapshot")
