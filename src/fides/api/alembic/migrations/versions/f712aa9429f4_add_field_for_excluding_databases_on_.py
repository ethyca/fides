"""add field for excluding databases on MonitorConfig model

Revision ID: f712aa9429f4
Revises: 31493e48c1d8
Create Date: 2024-07-11 18:00:14.221036

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f712aa9429f4"
down_revision = "31493e48c1d8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "monitorconfig",
        sa.Column(
            "excluded_databases",
            sa.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("monitorconfig", "excluded_databases")
