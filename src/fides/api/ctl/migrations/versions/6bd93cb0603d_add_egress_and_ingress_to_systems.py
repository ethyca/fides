"""Add egress and ingress to Systems

Revision ID: 6bd93cb0603d
Revises: 4fc34906c389
Create Date: 2022-09-21 00:27:35.164295

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6bd93cb0603d"
down_revision = "4fc34906c389"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ctl_systems", sa.Column("egress", sa.JSON()))
    op.add_column("ctl_systems", sa.Column("ingress", sa.JSON()))


def downgrade():
    op.drop_column("ctl_systems", "egress")
    op.drop_column("ctl_systems", "ingress")
