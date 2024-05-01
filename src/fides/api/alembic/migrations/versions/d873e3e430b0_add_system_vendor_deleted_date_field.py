"""add system vendor_deleted_date field

Revision ID: d873e3e430b0
Revises: 9e83545ed9b6
Create Date: 2024-04-22 14:25:13.232408

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d873e3e430b0"
down_revision = "9e83545ed9b6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "ctl_systems",
        sa.Column("vendor_deleted_date", sa.DateTime(timezone=True), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("ctl_systems", "vendor_deleted_date")
    # ### end Alembic commands ###
