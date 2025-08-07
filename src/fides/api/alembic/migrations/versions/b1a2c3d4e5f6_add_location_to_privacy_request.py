"""add location to privacy request

Revision ID: b1a2c3d4e5f6
Revises: a7065df4dcf1
Create Date: 2025-08-06 18:15:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b1a2c3d4e5f6"
down_revision = "a7065df4dcf1"
branch_labels = None
depends_on = None


def upgrade():
    # Add location column to privacyrequest table
    op.add_column("privacyrequest", sa.Column("location", sa.String(), nullable=True))


def downgrade():
    # Remove location column from privacyrequest table
    op.drop_column("privacyrequest", "location")
