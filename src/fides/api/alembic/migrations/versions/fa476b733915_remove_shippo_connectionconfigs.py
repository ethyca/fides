"""remove Shippo connection configs

Revision ID: fa476b733915
Revises: 59d9c4beeb30
Create Date: 2024-10-03 17:16:42.070361

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "fa476b733915"
down_revision = "59d9c4beeb30"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        WITH shippo_connections AS (
            SELECT id
            FROM connectionconfig
            WHERE connection_type = 'saas'
              AND saas_config->>'type' = 'shippo'
        )
        DELETE FROM datasetconfig
        WHERE connection_config_id IN (SELECT id FROM shippo_connections);

        DELETE FROM connectionconfig WHERE connection_type = 'saas' AND saas_config->>'type' = 'shippo';
    """
    )


def downgrade():
    # cannot downgrade since we can't restore a deleted connectionconfig
    pass
