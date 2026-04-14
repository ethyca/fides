"""add steward_ids to stagedresource

Revision ID: a42ef09a3dfe
Revises: b3c8d5e7f2a1
Create Date: 2026-04-14 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = "a42ef09a3dfe"
down_revision = "b3c8d5e7f2a1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stagedresource",
        sa.Column("steward_ids", ARRAY(sa.String()), nullable=True),
    )


def downgrade():
    op.drop_column("stagedresource", "steward_ids")
