"""adding referer to authenticationrequest

Revision ID: 3a47ce736a37
Revises: 5abb65a8cb91
Create Date: 2023-07-18 03:38:18.238072

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3a47ce736a37"
down_revision = "5abb65a8cb91"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "authenticationrequest", sa.Column("referer", sa.String(), nullable=True)
    )


def downgrade():
    op.drop_column("authenticationrequest", "referer")
