"""add property id to privacy preference history

Revision ID: e62541eb26bc
Revises: fc2b2c06e595
Create Date: 2024-05-14 15:33:50.788760

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e62541eb26bc"
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
    op.create_foreign_key(
        "plus_property_id_fkey",
        "privacypreferencehistory",
        "plus_property",
        ["property_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "plus_property_id_fkey", "privacypreferencehistory", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_property_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "property_id")
