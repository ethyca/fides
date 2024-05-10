"""add property table

Revision ID: 26d5976531d6
Revises: 68cb26f3492d
Create Date: 2024-02-20 18:44:57.913009

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "26d5976531d6"
down_revision = "68cb26f3492d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_property",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_plus_property_key"), "plus_property", ["key"], unique=True)
    op.create_index(op.f("ix_plus_property_id"), "plus_property", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_plus_property_id"), table_name="plus_property")
    op.drop_index(op.f("ix_plus_property_key"), table_name="plus_property")
    op.drop_table("plus_property")
