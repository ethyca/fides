"""update discovery monitor config model frequency and databases

Revision ID: ad0109b041b3
Revises: fc2b2c06e595
Create Date: 2024-05-13 14:13:01.956663

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ad0109b041b3"
down_revision = "fc2b2c06e595"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "monitorconfig",
        sa.Column(
            "databases", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
    )
    op.add_column(
        "monitorconfig",
        sa.Column(
            "monitor_execution_trigger",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("monitorconfig", "monitor_execution_trigger")
    op.drop_column("monitorconfig", "databases")
