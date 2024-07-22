"""add consent automation table

Revision ID: 17c55911216f
Revises: f712aa9429f4
Create Date: 2024-07-22 21:36:45.948148

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "17c55911216f"
down_revision = "f712aa9429f4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_consent_automation",
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
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.Column(
            "consentable_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["connection_config_id"], ["connectionconfig.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plus_consent_automation_id"),
        "plus_consent_automation",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_plus_consent_automation_id"), table_name="plus_consent_automation"
    )
    op.drop_table("plus_consent_automation")
