"""custom asset table

Revision ID: 8c54e1e5bdc4
Revises: 66df7d9b8103
Create Date: 2023-09-22 03:10:38.544455

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8c54e1e5bdc4"
down_revision = "66df7d9b8103"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_custom_asset",
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
        sa.Column(
            "key", sa.Enum("custom_fides_css", name="customassettype"), nullable=False
        ),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plus_custom_asset_id"), "plus_custom_asset", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_plus_custom_asset_key"), "plus_custom_asset", ["key"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_plus_custom_asset_key"), table_name="plus_custom_asset")
    op.drop_index(op.f("ix_plus_custom_asset_id"), table_name="plus_custom_asset")
    op.drop_table("plus_custom_asset")
