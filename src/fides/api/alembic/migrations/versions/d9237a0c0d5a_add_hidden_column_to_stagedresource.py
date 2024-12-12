"""add `hidden` and `data_use` columns to stagedresource

Revision ID: d9237a0c0d5a
Revises: c90d46f6d3f2
Create Date: 2024-11-21 13:18:24.085858

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9237a0c0d5a"
down_revision = "c90d46f6d3f2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stagedresource", sa.Column("hidden", sa.Boolean(), nullable=False))
    op.add_column("stagedresource", sa.Column("data_use", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    op.drop_column("stagedresource", "hidden")
    op.drop_column("stagedresource", "data_use")
    # ### end Alembic commands ###
