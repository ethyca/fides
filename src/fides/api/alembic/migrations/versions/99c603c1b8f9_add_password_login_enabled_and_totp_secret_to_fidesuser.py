"""add password login enabled and totp secret to fidesuser

Revision ID: 99c603c1b8f9
Revises: 6e565c16dae1
Create Date: 2025-04-02 01:55:57.890545

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "99c603c1b8f9"
down_revision = "6e565c16dae1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "fidesuser",
        sa.Column(
            "password_login_enabled",
            sa.Boolean(),
            nullable=True,
        ),
    )
    op.add_column(
        "fidesuser",
        sa.Column(
            "totp_secret",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.alter_column("fidesuser", "hashed_password", nullable=True)
    op.alter_column("fidesuser", "salt", nullable=True)


def downgrade():
    op.alter_column("fidesuser", "hashed_password", nullable=False)
    op.alter_column("fidesuser", "salt", nullable=False)
    op.drop_column("fidesuser", "totp_secret")
    op.drop_column("fidesuser", "password_login_enabled")
