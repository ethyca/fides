"""Add system_history table

Revision ID: 093bb28a8270
Revises: 507563f6f8d4
Create Date: 2023-08-18 23:48:22.934916

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "093bb28a8270"
down_revision = "507563f6f8d4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_history",
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
        sa.Column("edited_by", sa.String(), nullable=False),
        sa.Column("system_key", sa.String(), nullable=False),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["system_key"], ["ctl_systems.fides_key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("system_history")
