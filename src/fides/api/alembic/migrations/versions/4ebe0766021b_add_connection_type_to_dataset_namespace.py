"""Add connection_type to dataset namespace meta

Revision ID: 4ebe0766021b
Revises: 36ad82edb38e
Create Date: 2024-10-16 15:25:08.544946

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4ebe0766021b"
down_revision = "36ad82edb38e"
branch_labels = None
depends_on = None


def upgrade():
    # Populate the connection_type field in the namespace meta for all datasets
    # that have a namespace key in their fides_meta json field.

    # If the namespace dict has a project_id key, we know it's a BigQuery dataset.
    op.execute(
        """
        update ctl_datasets
        set fides_meta = jsonb_set(fides_meta::jsonb, '{namespace, connection_type}', '"bigquery"', true)
        where (fides_meta::jsonb ? 'namespace') and ((fides_meta::jsonb ->> 'namespace')::jsonb ? 'project_id');
        """
    )

    # If the namespace dict has a database_instance_id, we know it's an RDS MySQL dataset.
    op.execute(
        """
        update ctl_datasets
        set fides_meta = jsonb_set(fides_meta::jsonb, '{namespace, connection_type}', '"rds_mysql"', true)
        where (fides_meta::jsonb ? 'namespace') and ((fides_meta::jsonb ->> 'namespace')::jsonb ? 'database_instance_id');
        """
    )


def downgrade():
    # Remove the connection_type field from the namespace meta for all datasets
    # that have a namespace key in their fides_meta json field.
    op.execute(
        """
        update ctl_datasets
        set fides_meta  = fides_meta::jsonb #- '{namespace, connection_type}'
        where fides_meta::jsonb ? 'namespace';
        """
    )
