"""add email verification token table

Revision ID: 835de27d8c76
Revises: e3f4a5b6c7d8
Create Date: 2026-05-12 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "835de27d8c76"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fides_user_email_verification",
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
        op.f("ix_fides_user_email_verification_id"),
        "fides_user_email_verification",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fides_user_email_verification_user_id"),
        "fides_user_email_verification",
        ["user_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f("ix_fides_user_email_verification_user_id"),
        table_name="fides_user_email_verification",
    )
    op.drop_index(
        op.f("ix_fides_user_email_verification_id"),
        table_name="fides_user_email_verification",
    )
    op.drop_table("fides_user_email_verification")
