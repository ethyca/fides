"""add property path

Revision ID: d7feff990012
Revises: 0debabbb9c6a
Create Date: 2024-05-15 00:20:47.115547

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d7feff990012"
down_revision = "0debabbb9c6a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_property_path",
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
        sa.Column("property_id", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["plus_property.id"],
        ),
        sa.PrimaryKeyConstraint("id", "property_id"),
    )
    op.create_index(
        op.f("ix_plus_property_path_id"), "plus_property_path", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_plus_property_path_path"), "plus_property_path", ["path"], unique=True
    )
    op.create_index(
        op.f("ix_plus_property_path_property_id"),
        "plus_property_path",
        ["property_id"],
        unique=False,
    )
    op.drop_column("plus_property", "paths")


def downgrade():
    op.add_column(
        "plus_property",
        sa.Column(
            "paths",
            postgresql.ARRAY(sa.VARCHAR()),
            server_default=sa.text("'{}'::character varying[]"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_index(
        op.f("ix_plus_property_path_property_id"), table_name="plus_property_path"
    )
    op.drop_index(op.f("ix_plus_property_path_path"), table_name="plus_property_path")
    op.drop_index(op.f("ix_plus_property_path_id"), table_name="plus_property_path")
    op.drop_table("plus_property_path")
