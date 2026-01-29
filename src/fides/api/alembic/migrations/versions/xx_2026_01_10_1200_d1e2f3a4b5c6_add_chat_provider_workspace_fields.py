"""add chat provider workspace fields

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-01-10 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chat_provider_config",
        sa.Column("workspace_name", sa.String(), nullable=True),
    )
    op.add_column(
        "chat_provider_config",
        sa.Column("connected_by_email", sa.String(), nullable=True),
    )
    op.add_column(
        "chat_provider_config",
        sa.Column("notification_channel_id", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("chat_provider_config", "notification_channel_id")
    op.drop_column("chat_provider_config", "connected_by_email")
    op.drop_column("chat_provider_config", "workspace_name")
