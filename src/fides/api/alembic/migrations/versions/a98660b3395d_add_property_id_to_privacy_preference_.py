"""add property id to privacy preference history

Revision ID: a98660b3395d
Revises: fc2b2c06e595
Create Date: 2024-05-13 17:05:57.966211

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a98660b3395d"
down_revision = "fc2b2c06e595"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacypreferencehistory", sa.Column("property_id", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_property_id"),
        "privacypreferencehistory",
        ["property_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacypreferencehistory_property_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "property_id")
