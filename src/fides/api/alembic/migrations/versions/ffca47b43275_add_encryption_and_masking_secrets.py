"""add encryption and masking secrets to privacy request

Revision ID: ffca47b43275
Revises: 68cb26f3492d
Create Date: 2024-02-12 23:06:23.868617

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "ffca47b43275"
down_revision = "68cb26f3492d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacyrequest",
        sa.Column(
            "encryption",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "masking_secrets",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("privacyrequest", "masking_secrets")
    op.drop_column("privacyrequest", "encryption")
