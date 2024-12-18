"""add `data_uses` columns to stagedresource

Revision ID: d9237a0c0d5a
Revises: e5ec30dfcd87
Create Date: 2024-11-21 13:18:24.085858

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9237a0c0d5a"
down_revision = "e5ec30dfcd87"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stagedresource", sa.Column("data_uses", sa.ARRAY(sa.String), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_column("stagedresource", "data_uses")
    # ### end Alembic commands ###
