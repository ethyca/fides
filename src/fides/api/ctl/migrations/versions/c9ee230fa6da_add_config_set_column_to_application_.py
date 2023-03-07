"""add config_set column to application settings

Revision ID: c9ee230fa6da
Revises: 8e198eb13802
Create Date: 2023-02-01 15:13:52.133075

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9ee230fa6da"
down_revision = "8e198eb13802"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "applicationconfig",
        sa.Column(
            "config_set",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=False,
        ),
    )

    # include this update here to make up for an earlier miss when creating the table
    op.alter_column("applicationconfig", "api_set", nullable=False)


def downgrade():
    op.drop_column("applicationconfig", "config_set")

    # add a downgrade here for consistency
    op.alter_column("applicationconfig", "api_set", nullable=True)
