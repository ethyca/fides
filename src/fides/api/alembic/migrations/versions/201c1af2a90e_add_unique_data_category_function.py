"""add unique data category function

Revision ID: 201c1af2a90e
Revises: c90d46f6d3f2
Create Date: 2024-12-13 01:37:43.709477

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "201c1af2a90e"
down_revision = "c90d46f6d3f2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION get_unique_data_categories(dataset_refs text[])
        RETURNS text[] AS $$
            WITH categories AS (
                SELECT jsonb_array_elements_text(
                    jsonb_path_query(collections::jsonb, '$.** ? (@.data_categories != null).data_categories')
                ) AS category
                FROM ctl_datasets
                WHERE fides_key = ANY(dataset_refs)
            )
            SELECT COALESCE(
                array_agg(DISTINCT category),
                ARRAY[]::text[]
            )
            FROM categories;
        $$ LANGUAGE sql STABLE;
        """
    )


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS get_unique_data_categories(text[]);")
