"""add chat config

Revision ID: c1d2e3f4a5b6
Revises: 6d5f70dd0ba5
Create Date: 2026-01-14 12:00:00.000000

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "6d5f70dd0ba5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_config",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("provider_type", sa.String(), nullable=False, server_default="slack"),
        sa.Column("workspace_url", sa.String(), nullable=True),
        sa.Column("client_id", sa.String(), nullable=True),
        sa.Column(
            "client_secret",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "access_token",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "signing_secret",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("workspace_name", sa.String(), nullable=True),
        sa.Column("connected_by_email", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_url", name="chat_config_workspace_url_unique"),
    )
    op.create_index(
        op.f("ix_chat_config_id"), "chat_config", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_chat_config_id"), table_name="chat_config")
    op.drop_table("chat_config")
