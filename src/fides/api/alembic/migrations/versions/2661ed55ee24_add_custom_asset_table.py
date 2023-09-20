"""add custom asset table

Revision ID: 2661ed55ee24
Revises: 66df7d9b8103
Create Date: 2023-09-20 18:15:59.632376

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2661ed55ee24"
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
        sa.Column("key", sa.Enum("fides_css", name="customassettype"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plus_custom_asset_key"),
        "plus_custom_asset",
        ["key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_plus_custom_asset_id"), "plus_custom_asset", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_plus_custom_asset_id"), table_name="plus_custom_asset")
    op.drop_index(op.f("ix_plus_custom_asset_key"), table_name="plus_custom_asset")
    op.drop_table("plus_custom_asset")
