"""add custom report table

Revision ID: c9abc9bbaa49
Revises: fa476b733915
Create Date: 2024-09-26 23:19:58.766385

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c9abc9bbaa49"
down_revision = "fa476b733915"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_custom_report",
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
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["fidesuser.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_plus_custom_report_id"), "plus_custom_report", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_plus_custom_report_id"), table_name="plus_custom_report")
    op.drop_table("plus_custom_report")
