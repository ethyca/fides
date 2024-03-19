"""add privacy center config

Revision ID: 2e9aba76c322
Revises: 69e51a460e66
Create Date: 2024-03-14 22:17:45.544448

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2e9aba76c322"
down_revision = "69e51a460e66"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_privacy_center_config",
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
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("single_row", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "single_row", name="plus_privacy_center_config_single_row_check"
        ),
        sa.UniqueConstraint(
            "single_row", name="plus_privacy_center_config_single_row_unique"
        ),
    )
    op.create_index(
        op.f("ix_plus_privacy_center_config_id"),
        "plus_privacy_center_config",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_plus_privacy_center_config_id"),
        table_name="plus_privacy_center_config",
    )
    op.drop_table("plus_privacy_center_config")
