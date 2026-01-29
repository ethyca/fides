"""add chat provider signing secret

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-01-14 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chat_provider_config",
        sa.Column("signing_secret", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("chat_provider_config", "signing_secret")
