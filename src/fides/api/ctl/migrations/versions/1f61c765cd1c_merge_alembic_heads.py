"""Merge alembic heads

Revision ID: 1f61c765cd1c
Revises: 8f84fad4e00b, b72541d79f10
Create Date: 2022-12-02 17:59:08.490577

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1f61c765cd1c"
down_revision = ("8f84fad4e00b", "b72541d79f10")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
