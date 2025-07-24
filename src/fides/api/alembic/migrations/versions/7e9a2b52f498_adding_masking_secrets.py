"""adding masking secrets

Revision ID: 7e9a2b52f498
Revises: d0031087eacb
Create Date: 2024-12-23 23:29:53.557951

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "7e9a2b52f498"
down_revision = "d0031087eacb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "masking_secret",
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
        sa.Column("privacy_request_id", sa.String(), nullable=False),
        sa.Column(
            "secret",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=False,
        ),
        sa.Column("masking_strategy", sa.String(), nullable=False),
        sa.Column(
            "secret_type",
            sa.String(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"], ["privacyrequest.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_masking_secret_id"), "masking_secret", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_masking_secret_id"), table_name="masking_secret")
    op.drop_table("masking_secret")
