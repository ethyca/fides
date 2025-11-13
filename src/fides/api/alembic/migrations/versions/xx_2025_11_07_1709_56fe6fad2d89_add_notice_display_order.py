"""add_notice_display_order

Revision ID: 56fe6fad2d89
Revises: b2c3d4e5f6a7
Create Date: 2025-11-07 17:09:24.917188

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "56fe6fad2d89"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    """
    Add display_order column to experiencenotices and privacynotice tables.

    This allows:
    1. Experiences to control the order in which notices are displayed in the API response
    2. Parent notices to control the order in which child notices are displayed

    Both enable drag-and-drop reordering in the Admin UI.
    """
    # Add display_order to experiencenotices for ordering notices within an experience
    op.add_column(
        "experiencenotices",
        sa.Column("display_order", sa.Integer(), nullable=True),
    )

    # Add display_order to privacynotice for ordering child notices within a parent
    op.add_column(
        "privacynotice",
        sa.Column("display_order", sa.Integer(), nullable=True),
    )


def downgrade():
    """
    Remove display_order column from experiencenotices and privacynotice tables.
    """
    op.drop_column("experiencenotices", "display_order")
    op.drop_column("privacynotice", "display_order")
