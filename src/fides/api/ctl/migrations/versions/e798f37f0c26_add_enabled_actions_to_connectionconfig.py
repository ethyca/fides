"""add enabled_actions to connectionconfig

Revision ID: e798f37f0c26
Revises: 63b482f5b49b
Create Date: 2023-05-11 17:54:05.476225

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e798f37f0c26"
down_revision = "63b482f5b49b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "connectionconfig",
        sa.Column(
            "enabled_actions",
            postgresql.ARRAY(sa.String()),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("connectionconfig", "enabled_actions")
