"""add replaceable field to custom_connector_template

Revision ID: ff782b0dc07e
Revises: 6d6b0b7cbb36
Create Date: 2023-03-29 23:41:26.164600

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ff782b0dc07e"
down_revision = "6d6b0b7cbb36"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "custom_connector_template",
        sa.Column(
            "replaceable", sa.Boolean(), unique=False, nullable=False, default=False
        ),
    )


def downgrade():
    op.drop_column("custom_connector_template", "replaceable")
