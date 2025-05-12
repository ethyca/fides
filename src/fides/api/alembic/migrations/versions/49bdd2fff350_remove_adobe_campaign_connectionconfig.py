"""empty message

Revision ID: 49bdd2fff350
Revises: c9abc9bbaa49
Create Date: 2024-10-09 16:02:06.996661

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "49bdd2fff350"
down_revision = "c9abc9bbaa49"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        WITH adobe_campaign_connections AS (
            SELECT id
            FROM connectionconfig
            WHERE connection_type = 'saas'
              AND saas_config->>'type' = 'adobe_campaign'
        )
        DELETE FROM datasetconfig
        WHERE connection_config_id IN (SELECT id FROM adobe_campaign_connections);

        DELETE FROM connectionconfig WHERE connection_type = 'saas' AND saas_config->>'type' = 'adobe_campaign';
    """
    )


def downgrade():
    # cannot downgrade since we can't restore a deleted connectionconfig
    pass
