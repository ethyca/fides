"""remove deprecated data uses for fideslang 1.4

Revision ID: 5307999c0dac
Revises: 76c02f99eec1
Create Date: 2023-06-11 11:15:53.386526

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5307999c0dac"
down_revision = "76c02f99eec1"
branch_labels = None
depends_on = None


def upgrade():
    # Remove all "default" Data uses

    # Insert the new default data uses
    pass


def downgrade():
    pass
