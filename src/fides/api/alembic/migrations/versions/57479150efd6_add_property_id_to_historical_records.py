"""add property id to historical records

Revision ID: 57479150efd6
Revises: fc2b2c06e595
Create Date: 2024-05-14 18:26:57.646508

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "57479150efd6"
down_revision = "ad0109b041b3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacypreferencehistory", sa.Column("property_id", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("property_id", sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column("servednoticehistory", "property_id")
    op.drop_column("privacypreferencehistory", "property_id")
