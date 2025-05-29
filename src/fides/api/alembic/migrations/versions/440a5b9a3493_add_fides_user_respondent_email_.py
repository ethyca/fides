"""Add fides_user_respondent_email_verification table

Revision ID: 440a5b9a3493
Revises: d0cbfec0b2dd
Create Date: 2025-05-29 15:41:59.521940

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "440a5b9a3493"
down_revision = "d0cbfec0b2dd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fides_user_respondent_email_verification",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column(
            "access_token_expires_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("verification_code", sa.String(), nullable=True),
        sa.Column(
            "verification_code_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["username"],
            ["fidesuser.username"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["fidesuser.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fides_user_respondent_email_verification_id",
        "fides_user_respondent_email_verification",
        ["id"],
        unique=True,
    )
    op.create_index(
        "ix_fides_user_respondent_email_verification_access_token",
        "fides_user_respondent_email_verification",
        ["access_token"],
        unique=True,
    )
    op.create_index(
        "ix_fides_user_respondent_email_verification_user_id",
        "fides_user_respondent_email_verification",
        ["user_id"],
    )


def downgrade():
    op.drop_index(
        "ix_fides_user_respondent_email_verification_user_id",
        table_name="fides_user_respondent_email_verification",
    )
    op.drop_index(
        "ix_fides_user_respondent_email_verification_access_token",
        table_name="fides_user_respondent_email_verification",
    )
    op.drop_index(
        "ix_fides_user_respondent_email_verification_id",
        table_name="fides_user_respondent_email_verification",
    )
    op.drop_table("fides_user_respondent_email_verification")
