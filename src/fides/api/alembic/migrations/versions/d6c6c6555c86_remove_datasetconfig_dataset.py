"""Remove datasetconfig dataset

Revision ID: d6c6c6555c86
Revises: 9c6f62e4c9da
Create Date: 2022-12-20 20:44:32.840423

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d6c6c6555c86"
down_revision = "9c6f62e4c9da"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("datasetconfig", "dataset")


def downgrade():
    op.add_column(
        "datasetconfig",
        sa.Column(
            "dataset",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
    )
