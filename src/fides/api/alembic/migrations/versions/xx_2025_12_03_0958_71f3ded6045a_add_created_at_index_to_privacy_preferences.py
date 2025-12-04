"""add created_at index to privacy_preferences

Revision ID: 71f3ded6045a
Revises:     795f46f656c0
Create Date: 2025-12-03 09:58:09.225767

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "71f3ded6045a"
down_revision = "795f46f656c0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        op.f("ix_privacy_preferences_created_at"),
        "privacy_preferences",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacy_preferences_created_at"), table_name="privacy_preferences"
    )
