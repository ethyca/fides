"""adding property id to historical records

Revision ID: 57479150efd6
Revises: fc2b2c06e595
Create Date: 2024-05-14 18:26:57.646508

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "57479150efd6"
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
    op.add_column(
        "servednoticehistory", sa.Column("property_id", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_servednoticehistory_property_id"),
        "servednoticehistory",
        ["property_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_servednoticehistory_property_id"), table_name="servednoticehistory"
    )
    op.drop_column("servednoticehistory", "property_id")
    op.drop_index(
        op.f("ix_privacypreferencehistory_property_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "property_id")
