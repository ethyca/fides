"""add monitors to client

Revision ID: a1b2c3d4e5f7
Revises: c1d2e3f4a5b6
Create Date: 2026-02-02 02:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "client",
        sa.Column(
            "monitors", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
    )


def downgrade():
    op.drop_column("client", "monitors")
