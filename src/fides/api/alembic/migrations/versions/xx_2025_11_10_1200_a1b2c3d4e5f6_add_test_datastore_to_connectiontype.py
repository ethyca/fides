"""Add test_datastore to ConnectionType

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2025-11-10 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    # Add test_datastore to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('attentive_email', 'bigquery', 'datahub', 'dynamodb', 'fides', 'generic_consent_email', 'generic_erasure_email', 'dynamic_erasure_email', 'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', 'manual', 'manual_webhook', 'manual_task', 'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', 'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', 'snowflake', 'sovrn', 'test_datastore', 'test_website', 'timescale', 'website')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # First remove the ConnectionConfigs with connection_type = 'test_datastore'
    op.execute(
        "delete from connectionconfig where connection_type in ('test_datastore')"
    )
    # Then remove 'test_datastore' from ConnectionType enum by renaming old enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    # Create a new enum without 'test_datastore'
    op.execute(
        "create type connectiontype as enum('attentive_email', 'bigquery', 'datahub', 'dynamodb', 'fides', 'generic_consent_email', 'generic_erasure_email', 'dynamic_erasure_email', 'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', 'manual', 'manual_webhook', 'manual_task', 'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', 'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', 'snowflake', 'sovrn', 'test_website', 'timescale', 'website')"
    )
    # Alter the connectionconfig table to use the new enum
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    # Drop the old enum
    op.execute("drop type connectiontype_old")
