"""Updating Attentive connection to Attentive email

Revision ID: 59d9c4beeb30
Revises: 75bb9ee843f5
Create Date: 2024-09-24 14:52:49.199323

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "59d9c4beeb30"
down_revision = "75bb9ee843f5"
branch_labels = None
depends_on = None


def upgrade():
    # Note: Since we may have live references to attentive
    # add 'attentive_email' to ConnectionType enum
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")
    op.execute(
        """
        CREATE TYPE connectiontype AS ENUM (
            'mongodb',
            'mysql',
            'https',
            'snowflake',
            'redshift',
            'mssql',
            'mariadb',
            'bigquery',
            'saas',
            'manual',
            'manual_webhook',
            'timescale',
            'fides',
            'sovrn',
            'attentive',
            'attentive_email',
            'dynamodb',
            'postgres',
            'generic_consent_email',
            'generic_erasure_email',
            'scylla',
            's3',
            'google_cloud_sql_mysql',
            'google_cloud_sql_postgres',
            'dynamic_erasure_email'
            'rds_mysql'
        )
    """
    )
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_old")

    # update connectionconfig reference from 'attentive' to 'attentive_email'
    op.execute(
        """
        UPDATE connectionconfig
        SET connection_type = 'attentive_email'::connectiontype
        WHERE connection_type = 'attentive'::connectiontype
        """
    )

    # remove 'attentive' from ConnectionType enum
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_staging")

    op.execute(
        """
        CREATE TYPE connectiontype AS ENUM (
            'mongodb',
            'mysql',
            'https',
            'snowflake',
            'redshift',
            'mssql',
            'mariadb',
            'bigquery',
            'saas',
            'manual',
            'manual_webhook',
            'timescale',
            'fides',
            'sovrn',
            'attentive_email',
            'dynamodb',
            'postgres',
            'generic_consent_email',
            'generic_erasure_email',
            'scylla',
            's3',
            'google_cloud_sql_mysql',
            'google_cloud_sql_postgres',
            'dynamic_erasure_email',
            'rds_mysql'
        )
    """
    )
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_staging")


def downgrade():
    # add 'attentive' to ConnectionType enum
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")
    op.execute(
        """
        CREATE TYPE connectiontype AS ENUM (
            'mongodb',
            'mysql',
            'https',
            'snowflake',
            'redshift',
            'mssql',
            'mariadb',
            'bigquery',
            'saas',
            'manual',
            'manual_webhook',
            'timescale',
            'fides',
            'sovrn',
            'attentive',
            'attentive_email',
            'dynamodb',
            'postgres',
            'generic_consent_email',
            'generic_erasure_email',
            'scylla',
            's3',
            'google_cloud_sql_mysql',
            'google_cloud_sql_postgres',
            'dynamic_erasure_email',
            'rds_mysql'
        )
    """
    )
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_old")

    # update connectionconfig reference from 'attentive_email' to 'attentive'
    op.execute(
        """
        UPDATE connectionconfig
        SET connection_type = 'attentive'::connectiontype
        WHERE connection_type = 'attentive_email'::connectiontype
        """
    )

    # remove 'attentive_email' from ConnectionType enum
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_staging")

    op.execute(
        """
        CREATE TYPE connectiontype AS ENUM (
            'mongodb',
            'mysql',
            'https',
            'snowflake',
            'redshift',
            'mssql',
            'mariadb',
            'bigquery',
            'saas',
            'manual',
            'manual_webhook',
            'timescale',
            'fides',
            'sovrn',
            'attentive',
            'dynamodb',
            'postgres',
            'generic_consent_email',
            'generic_erasure_email',
            'scylla',
            's3',
            'google_cloud_sql_mysql',
            'google_cloud_sql_postgres',
            'dynamic_erasure_email'
        )
    """
    )

    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_staging")
