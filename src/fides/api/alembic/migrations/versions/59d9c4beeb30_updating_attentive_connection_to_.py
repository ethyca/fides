"""Updating Attentive connection to Attentive email

Revision ID: 59d9c4beeb30
Revises: 9de4bb76307a
Create Date: 2024-09-24 14:52:49.199323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59d9c4beeb30'
down_revision = '9de4bb76307a'
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
    #update connectionconfig reference from 'attentive' to 'attentive_email'

    #remove 'attentive' from ConnectionType enum
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
    pass


def downgrade():
    # add 'attentive' to ConnectionType enum

    #update connectionconfig reference from 'attentive_email' to 'attentive'

    #remove 'attentive_email' from ConnectionType enum
    pass
