"""add email_verified_at and password reset token table

Revision ID: d4e5f6a7b8c9
Revises: b5d8f2a3c6e9
Create Date: 2026-04-03 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "d4e6f8a0b2c3"
branch_labels = None
depends_on = None


def upgrade():
    # Add email_verified_at to fidesuser
    op.add_column(
        "fidesuser",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create password reset token table
    op.create_table(
        "fides_user_password_reset",
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
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("hashed_token", sa.String(), nullable=False),
        sa.Column("salt", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["fidesuser.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_fides_user_password_reset_user_id",
        "fides_user_password_reset",
        ["user_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_fides_user_password_reset_user_id",
        table_name="fides_user_password_reset",
    )
    op.drop_table("fides_user_password_reset")
    op.drop_column("fidesuser", "email_verified_at")
