"""make datasetconfig.ctl_datasets non-nullable

Revision ID: 9c6f62e4c9da
Revises: 216cdc7944f1
Create Date: 2022-12-09 23:56:13.022119

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c6f62e4c9da"
down_revision = "216cdc7944f1"
branch_labels = None
depends_on = None


def upgrade():
    """Followup migration to make datasetconfig.ctl_dataset_id non nullable"""
    op.alter_column(
        "datasetconfig", "ctl_dataset_id", existing_type=sa.VARCHAR(), nullable=False
    )


def downgrade():
    op.alter_column(
        "datasetconfig", "ctl_dataset_id", existing_type=sa.VARCHAR(), nullable=True
    )
