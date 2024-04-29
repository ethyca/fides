"""privacy request stopped

Revision ID: 27fe9da9d0f9
Revises: 1ff88b7bd579
Create Date: 2022-06-06 20:28:08.893135

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "27fe9da9d0f9"
down_revision = "1ff88b7bd579"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacyrequest",
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("privacyrequest", "paused_at")
