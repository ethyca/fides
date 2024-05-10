"""Add banner_description to experience config

Revision ID: f396c1f84b0f
Revises: 4ced99dabebb
Create Date: 2024-01-02 01:35:41.813279

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f396c1f84b0f"
down_revision = "4ced99dabebb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_description", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("banner_description", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_title", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("banner_title", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("privacyexperienceconfighistory", "banner_title")
    op.drop_column("privacyexperienceconfig", "banner_title")
    op.drop_column("privacyexperienceconfighistory", "banner_description")
    op.drop_column("privacyexperienceconfig", "banner_description")
