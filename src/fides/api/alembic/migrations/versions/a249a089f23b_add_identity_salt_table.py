"""add identity salt table

Revision ID: a249a089f23b
Revises: 784f145ec892
Create Date: 2024-09-04 23:10:42.920719

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "a249a089f23b"
down_revision = "784f145ec892"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "identity_salt",
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
        sa.Column(
            "encrypted_value",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("single_row", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("single_row", name="identity_salt_single_row_check"),
        sa.UniqueConstraint("single_row", name="identity_salt_single_row_unique"),
    )
    op.create_index(op.f("ix_identity_salt_id"), "identity_salt", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_identity_salt_id"), table_name="identity_salt")
    op.drop_table("identity_salt")
