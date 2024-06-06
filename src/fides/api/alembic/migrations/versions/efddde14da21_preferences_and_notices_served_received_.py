"""preferences and notices_served received at

Revision ID: efddde14da21
Revises: 4b2eade4353c
Create Date: 2024-05-29 16:17:23.357583

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "efddde14da21"
down_revision = "4b2eade4353c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacypreferencehistory",
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("servednoticehistory", "received_at")
    op.drop_column("privacypreferencehistory", "received_at")
