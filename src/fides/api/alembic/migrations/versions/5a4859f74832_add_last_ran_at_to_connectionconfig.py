"""Add last_ran_at to ConnectionConfig

Revision ID: 5a4859f74832
Revises: c9a22b284afa
Create Date: 2024-10-22 14:58:09.174708

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a4859f74832"
down_revision = "c9a22b284afa"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "connectionconfig",
        sa.Column("last_ran_at", sa.DateTime(timezone=True), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("connectionconfig", "last_ran_at")
    # ### end Alembic commands ###