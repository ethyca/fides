"""Add access review approval columns and status enum value

Adds nullable columns for tracking admin approval of access packages
before delivery: approved_at timestamp and approved_by user reference.
Also adds the 'awaiting_access_review' status to the privacyrequeststatus enum.

Revision ID: e8f9a1b2c3d4
Revises: d7e8f9a0b1c2
Create Date: 2026-04-24 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e8f9a1b2c3d4"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE privacyrequeststatus ADD VALUE IF NOT EXISTS 'awaiting_access_review'"
    )
    op.add_column(
        "privacyrequest",
        sa.Column("access_review_approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "privacyrequest",
        sa.Column("access_review_approved_by", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("privacyrequest", "access_review_approved_by")
    op.drop_column("privacyrequest", "access_review_approved_at")
    # Note: PostgreSQL does not support removing enum values.
    # The 'awaiting_access_review' value will remain in the enum type.
