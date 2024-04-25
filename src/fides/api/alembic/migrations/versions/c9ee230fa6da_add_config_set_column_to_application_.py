"""add config_set column to application settings

Revision ID: c9ee230fa6da
Revises: 8e198eb13802
Create Date: 2023-02-01 15:13:52.133075

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql.elements import TextClause
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import JSONTypeOverride
from fides.config import CONFIG

# revision identifiers, used by Alembic.
revision = "c9ee230fa6da"
down_revision = "8e198eb13802"
branch_labels = None
depends_on = None


def upgrade():
    encryptor = sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(
        JSONTypeOverride,
        CONFIG.security.app_encryption_key,
        AesGcmEngine,
        "pkcs5",
    )
    empty_obj = encryptor.process_bind_param({}, JSON)

    op.add_column(
        "applicationconfig",
        sa.Column(
            "config_set",
            StringEncryptedType(),
            nullable=False,
            server_default=empty_obj,
        ),
    )

    # reset the server_default now that it's initial value has been set
    op.alter_column(
        "applicationconfig", "config_set", nullable=False, server_default=None
    )

    # include this update here to make up for an earlier miss when creating the table
    op.alter_column("applicationconfig", "api_set", nullable=False)


def downgrade():
    op.drop_column("applicationconfig", "config_set")

    # add a downgrade here for consistency
    op.alter_column("applicationconfig", "api_set", nullable=True)
