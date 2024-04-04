"""drop key column from property

Revision ID: 3815b0db5b14
Revises: 32497f08e227
Create Date: 2024-02-29 21:54:38.751678

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3815b0db5b14"
down_revision = "32497f08e227"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_plus_property_key", table_name="plus_property")
    op.drop_column("plus_property", "key")


def downgrade():
    op.add_column(
        "plus_property",
        sa.Column("key", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index("ix_plus_property_key", "plus_property", ["key"], unique=False)
