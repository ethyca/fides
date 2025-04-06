"""add website connection type

Revision ID: c961528edfc6
Revises: 021166731846
Create Date: 2025-01-27 19:20:20.236548

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c961528edfc6"
down_revision = "021166731846"
branch_labels = None
depends_on = None


def upgrade():
    # add 'website' to ConnectionType enum
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
            'rds_mysql',
            'rds_postgres',
            'datahub',
            'website'
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


def downgrade():
    # Remove 'website' from ConnectionType enum
    op.execute("DELETE FROM connectionconfig WHERE connection_type IN ('datahub')")
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
            'rds_mysql',
            'rds_postgres',
            'datahub'
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
