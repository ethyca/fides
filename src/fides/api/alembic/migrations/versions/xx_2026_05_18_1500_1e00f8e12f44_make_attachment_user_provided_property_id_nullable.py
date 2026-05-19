"""make attachment_user_provided property_id nullable

Revision ID: 1e00f8e12f44
Revises: 9f21507db078
Create Date: 2026-05-18 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1e00f8e12f44"
down_revision = "9f21507db078"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "attachment_user_provided",
        "property_id",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "attachment_user_provided",
        "property_id",
        existing_type=sa.String(),
        nullable=False,
    )
