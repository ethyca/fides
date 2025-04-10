"""add unique to MonitorConfig

Revision ID: 26aa81a7623f
Revises: 9288f729cac4
Create Date: 2025-04-10 16:48:04.805848

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '26aa81a7623f'
down_revision = '9288f729cac4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(None, 'monitorconfig', ['name'])


def downgrade():
    op.drop_constraint(None, 'monitorconfig', type_='unique')
