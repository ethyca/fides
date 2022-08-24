"""merge ops and ctl migrations

Revision ID: 7b81d34352e8
Revises: 4fc34906c389, 7abe778b7082
Create Date: 2022-08-22 00:41:38.597943

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7b81d34352e8"
down_revision = ("4fc34906c389", "7abe778b7082")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
