"""Add access_package_redactions column to privacyrequest

Adds a nullable JSONB column to store redaction instructions for the
access package review workflow. Stores the list of field/record-level
redactions an admin has applied before approving the package for delivery.

Revision ID: d7e8f9a0b1c2
Revises: b3c8d5e7f2a1
Create Date: 2026-04-22 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "d7e8f9a0b1c2"
down_revision = "b3c8d5e7f2a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "privacyrequest",
        sa.Column("access_package_redactions", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("privacyrequest", "access_package_redactions")
