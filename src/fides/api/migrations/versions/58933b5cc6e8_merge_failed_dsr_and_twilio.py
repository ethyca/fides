"""Merge failed dsr and twilio

Revision ID: 58933b5cc6e8
Revises: 179f2bb623ae, 28108b17a99c
Create Date: 2022-11-14 21:26:49.027809

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "58933b5cc6e8"
down_revision = ("179f2bb623ae", "28108b17a99c")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
