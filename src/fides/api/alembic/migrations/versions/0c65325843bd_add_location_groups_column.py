"""add_location_groups_column

Revision ID: 0c65325843bd
Revises: a1e23b70f2b2
Create Date: 2024-02-21 19:56:39.228072

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0c65325843bd"
down_revision = "a1e23b70f2b2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "location_regulation_selections",
        sa.Column(
            "selected_location_groups",
            sa.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("location_regulation_selections", "selected_location_groups")
