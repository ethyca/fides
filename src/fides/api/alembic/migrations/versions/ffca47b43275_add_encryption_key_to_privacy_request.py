"""add encryption key and masking secrets to privacy request

Revision ID: ffca47b43275
Revises: 2e9aba76c322
Create Date: 2024-02-12 23:06:23.868617

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "ffca47b43275"
down_revision = "2e9aba76c322"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacyrequest",
        sa.Column(
            "encryption_key",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("privacyrequest", "encryption_key")
