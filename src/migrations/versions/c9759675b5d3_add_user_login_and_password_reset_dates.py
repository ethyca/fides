"""add user login and password reset dates

Revision ID: c9759675b5d3
Revises: 906d7198df28
Create Date: 2022-04-14 13:16:58.940571

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9759675b5d3"
down_revision = "906d7198df28"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "fidesopsuser",
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "fidesopsuser", sa.Column("password_reset_at", sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_column("fidesopsuser", "last_login_at")
    op.drop_column("fidesopsuser", "password_reset_at")
