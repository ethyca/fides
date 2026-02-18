"""Add is_encrypted column to privacy_preferences

Revision ID: d3f08ca31314
Revises: a0109cdde920
Create Date: 2026-02-18 18:14:26.751743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d3f08ca31314"
down_revision = "a0109cdde920"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacy_preferences",
        sa.Column("is_encrypted", sa.Boolean(), nullable=True),
    )
    op.execute("UPDATE privacy_preferences SET is_encrypted = true")
    op.alter_column("privacy_preferences", "is_encrypted", nullable=False)
    op.create_index(
        op.f("ix_privacy_preferences_is_encrypted"),
        "privacy_preferences",
        ["is_encrypted"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacy_preferences_is_encrypted"),
        table_name="privacy_preferences",
    )
    op.drop_column("privacy_preferences", "is_encrypted")
