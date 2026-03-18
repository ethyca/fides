"""add name to client

Revision ID: 38071fffda39
Revises: baa6792fc3f7
Create Date: 2026-03-13 16:58:07.889894

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38071fffda39'
down_revision = 'baa6792fc3f7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("client", sa.Column("name", sa.String(), nullable=True))
    op.add_column("client", sa.Column("description", sa.String(), nullable=True))


def downgrade():
    op.drop_column("client", "description")
    op.drop_column("client", "name")
