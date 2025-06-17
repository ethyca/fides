"""remove_replaceable_from_custom_connector_template

Revision ID: 5b8685afd90f
Revises: 29e56fa1fdb3
Create Date: 2025-06-13 13:46:14.417290

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5b8685afd90f"
down_revision = "29e56fa1fdb3"
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
