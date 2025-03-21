"""add order to experience notices

Revision ID: ffb9bd2dcd3f
Revises: 1d2f04ac19f2
Create Date: 2025-03-21 15:15:18.869533

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "ffb9bd2dcd3f"
down_revision = "1d2f04ac19f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "experiencenotices",
        sa.Column("order", postgresql.INTEGER, server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("experiencenotices", "order")
