"""staged resource web monitor updates

Revision ID: 58f8edd66b69
Revises: 1088e8353890
Create Date: 2024-12-17 19:25:36.184841

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "58f8edd66b69"
down_revision = "1088e8353890"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("stagedresource", sa.Column("system_id", sa.String(), nullable=True))
    op.add_column("stagedresource", sa.Column("vendor_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_stagedresource_monitor_config_id"),
        "stagedresource",
        ["monitor_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stagedresource_system_id"),
        "stagedresource",
        ["system_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stagedresource_vendor_id"),
        "stagedresource",
        ["vendor_id"],
        unique=False,
    )
    op.create_foreign_key(None, "stagedresource", "ctl_systems", ["system_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "stagedresource", type_="foreignkey")
    op.drop_index(op.f("ix_stagedresource_vendor_id"), table_name="stagedresource")
    op.drop_index(op.f("ix_stagedresource_system_id"), table_name="stagedresource")
    op.drop_index(
        op.f("ix_stagedresource_monitor_config_id"), table_name="stagedresource"
    )
    op.drop_column("stagedresource", "vendor_id")
    op.drop_column("stagedresource", "system_id")
    # ### end Alembic commands ###
