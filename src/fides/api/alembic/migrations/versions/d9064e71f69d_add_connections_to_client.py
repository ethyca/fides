"""add connections to client

Revision ID: d9064e71f69d
Revises: ffee79245c9a
Create Date: 2024-08-20 22:11:34.351186

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9064e71f69d"
down_revision = "ffee79245c9a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "client",
        sa.Column(
            "connections", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
    )


def downgrade():
    op.drop_column("client", "connections")
