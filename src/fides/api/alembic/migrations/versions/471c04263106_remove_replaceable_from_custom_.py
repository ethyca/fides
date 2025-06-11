"""remove_replaceable_from_custom_connector_template

Revision ID: 471c04263106
Revises: c586a56c25e7
Create Date: 2025-06-10 18:52:35.892660

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '471c04263106'
down_revision = 'c586a56c25e7'
branch_labels = None
depends_on = None


def upgrade():
    # remove the CustomConnectorTemplate.replaceable column as it's no longer needed
    op.drop_column("custom_connector_template", "replaceable")


def downgrade():
    # re-add the CustomConnectorTemplate.replaceable column
    op.add_column(
        "custom_connector_template",
        sa.Column(
            "replaceable", sa.Boolean(), unique=False, nullable=False, server_default=sa.text("false")
        ),
    )
