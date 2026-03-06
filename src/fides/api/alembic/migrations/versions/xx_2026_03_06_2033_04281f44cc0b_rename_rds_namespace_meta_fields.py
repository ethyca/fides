"""rename rds namespace meta fields

Revision ID: 04281f44cc0b
Revises: bf12f05ef8eb
Create Date: 2026-03-06 20:33:13.839629

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "04281f44cc0b"
down_revision = "bf12f05ef8eb"
branch_labels = None
depends_on = None


def upgrade():
    # Rename database_id → database_name in RDS Postgres namespace metadata.
    # The namespace dict is stored as JSON inside fides_meta on ctl_datasets.
    # We target only rows with connection_type = 'rds_postgres'.
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_id}',
            '{namespace, database_name}',
            fides_meta::jsonb #> '{namespace, database_id}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_postgres'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_id';
        """
    )

    # Rename database_instance_id → database_instance_name.
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_instance_id}',
            '{namespace, database_instance_name}',
            fides_meta::jsonb #> '{namespace, database_instance_id}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_postgres'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_instance_id';
        """
    )

    # Rename database_id → database_name in RDS MySQL namespace metadata.
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_id}',
            '{namespace, database_name}',
            fides_meta::jsonb #> '{namespace, database_id}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_mysql'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_id';
        """
    )

    # Rename database_instance_id → database_instance_name in RDS MySQL.
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_instance_id}',
            '{namespace, database_instance_name}',
            fides_meta::jsonb #> '{namespace, database_instance_id}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_mysql'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_instance_id';
        """
    )

    # Rename database_id → database_name in plain MySQL namespace metadata.
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_id}',
            '{namespace, database_name}',
            fides_meta::jsonb #> '{namespace, database_id}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'mysql'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_id';
        """
    )


def downgrade():
    # Reverse: database_name → database_id
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_name}',
            '{namespace, database_id}',
            fides_meta::jsonb #> '{namespace, database_name}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_postgres'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_name';
        """
    )

    # Reverse: database_instance_name → database_instance_id
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_instance_name}',
            '{namespace, database_instance_id}',
            fides_meta::jsonb #> '{namespace, database_instance_name}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_postgres'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_instance_name';
        """
    )

    # Reverse RDS MySQL: database_name → database_id
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_name}',
            '{namespace, database_id}',
            fides_meta::jsonb #> '{namespace, database_name}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_mysql'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_name';
        """
    )

    # Reverse RDS MySQL: database_instance_name → database_instance_id
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_instance_name}',
            '{namespace, database_instance_id}',
            fides_meta::jsonb #> '{namespace, database_instance_name}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'rds_mysql'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_instance_name';
        """
    )

    # Reverse plain MySQL: database_name → database_id
    op.execute(
        """
        UPDATE ctl_datasets
        SET fides_meta = jsonb_set(
            fides_meta::jsonb #- '{namespace, database_name}',
            '{namespace, database_id}',
            fides_meta::jsonb #> '{namespace, database_name}'
        )
        WHERE (fides_meta::jsonb #>> '{namespace, connection_type}') = 'mysql'
          AND (fides_meta::jsonb #> '{namespace}') ? 'database_name';
        """
    )
