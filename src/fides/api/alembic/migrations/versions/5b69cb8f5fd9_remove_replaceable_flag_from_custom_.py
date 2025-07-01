"""remove_replaceable_flag_from_custom_connector_template

Revision ID: 5b69cb8f5fd9
Revises: 6a76a1fa4f3f
Create Date: 2025-06-19 16:01:30.238333

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5b69cb8f5fd9"
down_revision = "aadfe83c5644"
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
            "replaceable",
            sa.Boolean(),
            unique=False,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
