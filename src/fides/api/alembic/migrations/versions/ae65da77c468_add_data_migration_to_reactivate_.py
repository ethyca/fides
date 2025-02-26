"""Add data migration to reactivate taxonomy nodes

Revision ID: ae65da77c468
Revises: 10c6b7709be3
Create Date: 2024-12-18 12:27:47.239489

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.sql.elements import TextClause

# revision identifiers, used by Alembic.
revision = "ae65da77c468"
down_revision = "10c6b7709be3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    This is a data migration to activate taxonomy nodes if it is de-active and has any children that are active

    E.g.
    Taxonomy Tree: A----B----C
                         \
                          ----D
    Current Active Fields: A (false), B (false), C (true), D (false)
    Upgrade Active Fields: A (true), B (true), C (true), D (false)
    """
    bind: Connection = op.get_bind()

    reactivate_data_categories_query: TextClause = text(
        """
        WITH RECURSIVE leaf_nodes AS (
            SELECT DISTINCT dc.fides_key
            FROM ctl_data_categories dc
            WHERE dc.fides_key NOT IN (
                SELECT DISTINCT parent_key 
                FROM ctl_data_categories 
                WHERE parent_key IS NOT NULL
            )
            AND dc.active = true
        ),
        parent_hierarchy AS (
            SELECT dc.fides_key, dc.parent_key
            FROM ctl_data_categories dc
            INNER JOIN leaf_nodes ln ON dc.fides_key = ln.fides_key
            
            UNION
            
            SELECT dc.fides_key, dc.parent_key
            FROM ctl_data_categories dc
            INNER JOIN parent_hierarchy ph ON dc.fides_key = ph.parent_key
        )
        UPDATE ctl_data_categories
        SET active = true
        WHERE fides_key IN (
            SELECT fides_key FROM parent_hierarchy
        )
        AND active = false;
        """
    )

    reactivate_data_uses_query: TextClause = text(
        """
        WITH RECURSIVE leaf_nodes AS (
            SELECT DISTINCT dc.fides_key
            FROM ctl_data_uses dc
            WHERE dc.fides_key NOT IN (
                SELECT DISTINCT parent_key 
                FROM ctl_data_uses 
                WHERE parent_key IS NOT NULL
            )
            AND dc.active = true
        ),
        parent_hierarchy AS (
            SELECT dc.fides_key, dc.parent_key
            FROM ctl_data_uses dc
            INNER JOIN leaf_nodes ln ON dc.fides_key = ln.fides_key
            
            UNION
            
            SELECT dc.fides_key, dc.parent_key
            FROM ctl_data_uses dc
            INNER JOIN parent_hierarchy ph ON dc.fides_key = ph.parent_key
        )
        UPDATE ctl_data_uses
        SET active = true
        WHERE fides_key IN (
            SELECT fides_key FROM parent_hierarchy
        )
        AND active = false;
        """
    )

    # Update ctl_data_categories
    bind.execute(reactivate_data_categories_query)

    # Update ctl_data_uses
    bind.execute(reactivate_data_uses_query)


def downgrade() -> None:
    """
    This migration does not support downgrades.
    """
    pass
