"""add errors to monitor execution

Revision ID: 3c58001ad310
Revises: bd875a8b5d96
Create Date: 2025-02-27 20:45:38.462604

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3c58001ad310"
down_revision = "bd875a8b5d96"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monitorexecution",
        sa.Column(
            "messages",
            sa.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("monitorexecution", "messages")
