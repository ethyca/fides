"""tcf_publisher_overrides

Revision ID: 5225ea4de265
Revises: 1af6950f4625
Create Date: 2023-11-27 15:35:07.679747

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5225ea4de265"
down_revision = "1af6950f4625"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tcf_publisher_overrides",
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
        sa.Column("purpose", sa.Integer(), nullable=False),
        sa.Column("is_included", sa.Boolean(), server_default="t", nullable=True),
        sa.Column("required_legal_basis", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tcf_publisher_overrides_id"),
        "tcf_publisher_overrides",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_tcf_publisher_overrides_id"), table_name="tcf_publisher_overrides"
    )
    op.drop_table("tcf_publisher_overrides")
