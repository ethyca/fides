"""drop legacy userregistration table

Revision ID: 25ffa8bf6a95
Revises: a1ca9ddf3c3c
Create Date: 2026-03-23 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "25ffa8bf6a95"
down_revision = "a1ca9ddf3c3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop table first; this also drops dependent indexes.
    op.execute("DROP TABLE IF EXISTS userregistration CASCADE")
    op.execute("DROP INDEX IF EXISTS ix_userregistration_id")


def downgrade() -> None:
    op.create_table(
        "userregistration",
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
        sa.Column("user_email", sa.String(), nullable=True),
        sa.Column("user_organization", sa.String(), nullable=True),
        sa.Column("analytics_id", sa.String(), nullable=False),
        sa.Column("opt_in", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analytics_id"),
    )
    op.create_index(
        op.f("ix_userregistration_id"),
        "userregistration",
        ["id"],
        unique=False,
    )
