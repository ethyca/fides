"""add google_cloud_sql_mysql to connectiontype

Revision ID: 7641ea685ea4
Revises: cb344673f633
Create Date: 2024-06-18 16:17:15.012408

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7641ea685ea4"
down_revision = "cb344673f633"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'google_cloud_sql_mysql' to ConnectionType enum
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
            'dynamodb',
            'postgres',
            'generic_consent_email',
            'generic_erasure_email',
            'scylla',
            's3',
            'google_cloud_sql_mysql'
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
    # Remove 'google_cloud_sql_mysql' from ConnectionType enum
    op.execute(
        "DELETE FROM connectionconfig WHERE connection_type IN ('google_cloud_sql_mysql')"
    )
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
            'dynamodb',
            'postgres',
            'generic_consent_email',
            'generic_erasure_email',
            'scylla',
            's3'
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
