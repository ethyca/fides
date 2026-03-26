"""add data_purposes column to ctl_datasets

Revision ID: c7e3a9b1d4f2
Revises: 25ffa8bf6a95
Create Date: 2026-03-25 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7e3a9b1d4f2"
down_revision = "25ffa8bf6a95"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ctl_datasets",
        sa.Column("data_purposes", sa.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ctl_datasets", "data_purposes")
