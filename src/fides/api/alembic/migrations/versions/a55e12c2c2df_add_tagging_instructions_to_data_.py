"""add_tagging_instructions_to_data_category

Revision ID: a55e12c2c2df
Revises: 65a1bc82ae09
Create Date: 2025-10-13 21:14:00.723464

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a55e12c2c2df"
down_revision = "65a1bc82ae09"
branch_labels = None
depends_on = None


def upgrade():
    """Add tagging_instructions column to ctl_data_categories table."""
    op.add_column(
        "ctl_data_categories",
        sa.Column("tagging_instructions", sa.Text(), nullable=True),
    )


def downgrade():
    """Remove tagging_instructions column from ctl_data_categories table."""
    op.drop_column("ctl_data_categories", "tagging_instructions")
