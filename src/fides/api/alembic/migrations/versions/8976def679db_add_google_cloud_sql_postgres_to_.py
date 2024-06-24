"""add google_cloud_sql_postgres to connectiontype

Revision ID: 8976def679db
Revises: 7641ea685ea4
Create Date: 2024-06-20 18:12:42.560977

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8976def679db"
down_revision = "7641ea685ea4"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'google_cloud_sql_postgres' to ConnectionType enum
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


def downgrade():
    # Remove 'google_cloud_sql_postgres' from ConnectionType enum
    op.execute(
        "DELETE FROM connectionconfig WHERE connection_type IN ('google_cloud_sql_postgres')"
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
