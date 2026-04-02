"""add case_sensitive to identity_definition

Revision ID: b5d8f2a3c6e9
Revises: a4b7c8d9e0f1
Create Date: 2026-04-01 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "b5d8f2a3c6e9"
down_revision = "a4b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "identity_definition",
        sa.Column(
            "case_sensitive",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade():
    op.drop_column("identity_definition", "case_sensitive")
