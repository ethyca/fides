"""Adds new fields to MessagingConfig for test info

Revision ID: fd7571bef683
Revises: b9bfa12c167b
Create Date: 2024-10-09 23:08:01.901592

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fd7571bef683"
down_revision = "b9bfa12c167b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "messagingconfig",
        sa.Column("last_test_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "messagingconfig", sa.Column("last_test_succeeded", sa.Boolean(), nullable=True)
    )


def downgrade():
    op.drop_column("messagingconfig", "last_test_succeeded")
    op.drop_column("messagingconfig", "last_test_timestamp")
