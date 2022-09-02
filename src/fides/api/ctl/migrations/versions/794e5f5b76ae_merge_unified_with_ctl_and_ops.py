"""merge unified with ctl and ops

Revision ID: 794e5f5b76ae
Revises: 25adddf820a3, c2f7a29c4780
Create Date: 2022-09-02 08:41:29.962231

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "794e5f5b76ae"
down_revision = ("25adddf820a3", "c2f7a29c4780")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
