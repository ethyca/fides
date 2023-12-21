"""add fides_user_invite table

Revision ID: 02d02f83ff11
Revises: 1ad4b29983da
Create Date: 2023-12-21 01:12:32.351994

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "02d02f83ff11"
down_revision = "a3abcf694cf3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fides_user_invite",
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
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_invite_code", sa.String(), nullable=False),
        sa.Column("salt", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", "username"),
    )
    op.create_index(
        op.f("ix_fides_user_invite_username"),
        "fides_user_invite",
        ["username"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fides_user_invite_id"), "fides_user_invite", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_fides_user_invite_id"), table_name="fides_user_invite")
    op.drop_index(op.f("ix_fides_user_invite_username"), table_name="fides_user_invite")
    op.drop_table("fides_user_invite")
