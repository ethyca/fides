"""add_active_column_taxonomy_elements

Revision ID: 5abb65a8cb91
Revises: 7c562441c589
Create Date: 2023-07-14 11:08:55.169966

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5abb65a8cb91"
down_revision = "7c562441c589"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ctl_data_categories",
        sa.Column("active", sa.BOOLEAN(), nullable=False, server_default="t"),
    )
    op.add_column(
        "ctl_data_subjects",
        sa.Column("active", sa.BOOLEAN(), nullable=False, server_default="t"),
    )
    op.add_column(
        "ctl_data_uses",
        sa.Column("active", sa.BOOLEAN(), nullable=False, server_default="t"),
    )
    op.add_column(
        "ctl_data_qualifiers",
        sa.Column("active", sa.BOOLEAN(), nullable=False, server_default="t"),
    )


def downgrade():
    op.drop_column("ctl_data_uses", "active")
    op.drop_column("ctl_data_subjects", "active")
    op.drop_column("ctl_data_categories", "active")
    op.drop_column("ctl_data_qualifiers", "active")
