"""add user_assigned_description to stagedresource

Revision ID: 6a42f48c23dd
Revises: d4e5f6a7b8c9
Create Date: 2026-04-07 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "6a42f48c23dd"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stagedresource",
        sa.Column("user_assigned_description", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("stagedresource", "user_assigned_description")
