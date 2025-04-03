"""adding login method and totp secret to fides user

Revision ID: 99c603c1b8f9
Revises: 67d01c4e124e
Create Date: 2025-04-02 01:55:57.890545

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "99c603c1b8f9"
down_revision = "67d01c4e124e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TYPE loginmethod AS ENUM ('username_password', 'sso')")
    op.add_column(
        "fidesuser",
        sa.Column(
            "login_method",
            sa.Enum("username_password", "sso", name="loginmethod"),
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
    op.drop_column("fidesuser", "login_method")
    op.execute("DROP TYPE loginmethod")
