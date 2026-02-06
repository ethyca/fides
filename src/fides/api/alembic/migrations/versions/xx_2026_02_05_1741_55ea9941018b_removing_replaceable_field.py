"""removing replaceable field

Revision ID: 55ea9941018b
Revises: a1b2c3d4e5f7
Create Date: 2026-02-05 17:41:37.038382

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "55ea9941018b"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("custom_connector_template", "replaceable")


def downgrade():
    op.add_column("custom_connector_template", sa.Column("replaceable", sa.BOOLEAN(), autoincrement=False, nullable=False))
