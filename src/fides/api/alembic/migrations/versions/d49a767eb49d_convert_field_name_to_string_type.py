"""convert field_name to string type

Revision ID: d49a767eb49d
Revises: 7799269e7078
Create Date: 2024-03-26 04:35:22.358246

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d49a767eb49d"
down_revision = "7799269e7078"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "providedidentity",
        "field_name",
        existing_type=sa.Enum("providedidentitytype"),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.add_column(
        "providedidentity", sa.Column("field_label", sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column("providedidentity", "field_label")
    op.alter_column(
        "providedidentity",
        "field_name",
        existing_type=sa.String(),
        type_=sa.Enum("providedidentitytype"),
        existing_nullable=False,
    )
