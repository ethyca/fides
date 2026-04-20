"""DEMO: feature migration that was developed on dev branch

This simulates a feature migration on the dev branch.
It shares the same down_revision as the hotfix migration,
creating two alembic heads (a multi-head scenario).

Revision ID: bbbb33334444
Revises: d6e7f8a9b0c1
Create Date: 2026-04-20 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bbbb33334444"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Simulated feature: add a column for a new feature on dev
    op.add_column(
        "privacyrequest",
        sa.Column("demo_feature_flag", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("privacyrequest", "demo_feature_flag")
