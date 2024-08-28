"""add openid_provider

Revision ID: ffee79245c9a
Revises: d69cf8f82a58
Create Date: 2024-08-09 19:27:07.222226

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "ffee79245c9a"
down_revision = "d69cf8f82a58"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "openid_provider",
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
        sa.Column("identifier", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column(
            "provider",
            sa.Enum("google", "okta", "custom", name="providerenum"),
            nullable=True,
        ),
        sa.Column(
            "client_id",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=False,
        ),
        sa.Column(
            "client_secret",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=False,
        ),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("authorization_url", sa.String(), nullable=True),
        sa.Column("token_url", sa.String(), nullable=True),
        sa.Column("user_info_url", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_openid_provider_id"), "openid_provider", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_openid_provider_identifier"),
        "openid_provider",
        ["identifier"],
        unique=True,
    )


def downgrade():
    op.drop_index(op.f("ix_openid_provider_identifier"), table_name="openid_provider")
    op.drop_index(op.f("ix_openid_provider_id"), table_name="openid_provider")
    op.drop_table("openid_provider")
    op.execute("DROP TYPE providerenum")
