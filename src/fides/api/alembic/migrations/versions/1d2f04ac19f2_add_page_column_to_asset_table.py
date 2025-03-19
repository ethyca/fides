"""
- add page column to asset table and
- change `Browser Request` values to `Browser request` StagedResource.resource_type column
- change `Browser Request` values to `Browser request` Asset.asset_type column

Revision ID: 1d2f04ac19f2
Revises: 7c3fbee90c78
Create Date: 2025-03-17 19:36:43.016383

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1d2f04ac19f2"
down_revision = "7c3fbee90c78"
branch_labels = None
depends_on = None


def upgrade():
    # adds page column to asset table
    op.add_column(
        "asset",
        sa.Column("page", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
    )

    # changes `Browser Request` values to `Browser request` in the two tables where it shows up`
    op.execute(
        "UPDATE stagedresource SET resource_type = 'Browser request' WHERE resource_type = 'Browser Request'"
    )
    op.execute(
        "UPDATE asset SET asset_type = 'Browser request' WHERE asset_type = 'Browser Request'"
    )


def downgrade():
    # drops page column from asset table
    op.drop_column("asset", "page")

    # changes `Browser request` values back to `Browser Request` in the two tables where it shows up
    op.execute(
        "UPDATE stagedresource SET resource_type = 'Browser Request' WHERE resource_type = 'Browser request'"
    )
    op.execute(
        "UPDATE asset SET asset_type = 'Browser Request' WHERE asset_type = 'Browser request'"
    )
