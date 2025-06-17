"""remove_replaceable_flag_from_custom_connector_template

Revision ID: d26175dc39b9
Revises: ba414a58ba90
Create Date: 2025-06-17 17:51:02.800113

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d26175dc39b9"
down_revision = "ba414a58ba90"
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
