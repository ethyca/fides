"""Add dynamic erasure email connector type

Revision ID: 9de4bb76307a
Revises: a249a089f23b
Create Date: 2024-09-10 11:36:35.020140

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9de4bb76307a"
down_revision = "a249a089f23b"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'dynamic_erasure_email' to ConnectionType enum
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


def downgrade():
    # Remove 'dynamic_erasure_email' from ConnectionType enum
    op.execute(
        "DELETE FROM connectionconfig WHERE connection_type IN ('dynamic_erasure_email')"
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
            's3',
            'google_cloud_sql_mysql',
            'google_cloud_sql_postgres'
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
