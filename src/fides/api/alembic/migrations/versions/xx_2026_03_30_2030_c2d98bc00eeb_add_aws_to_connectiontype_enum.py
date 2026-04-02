"""Add aws to ConnectionType enum

Revision ID: c2d98bc00eeb
Revises: b5d8f2a3c6e9
Create Date: 2026-03-30 20:30:29.871238

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c2d98bc00eeb"
down_revision = "b5d8f2a3c6e9"
branch_labels = None
depends_on = None

# Current enum values (before this migration)
_CURRENT_VALUES = (
    "'attentive_email', 'bigquery', 'datahub', 'dynamic_erasure_email', 'dynamodb', "
    "'entra', 'fides', 'generic_consent_email', 'generic_erasure_email', "
    "'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', "
    "'jira_ticket', 'manual', 'manual_task', 'manual_webhook', "
    "'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', "
    "'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', "
    "'snowflake', 'sovrn', 'test_datastore', 'test_website', 'timescale', 'website'"
)

# New enum values (after this migration)
_NEW_VALUES = (
    "'attentive_email', 'aws', 'bigquery', 'datahub', 'dynamic_erasure_email', 'dynamodb', "
    "'entra', 'fides', 'generic_consent_email', 'generic_erasure_email', "
    "'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', "
    "'jira_ticket', 'manual', 'manual_task', 'manual_webhook', "
    "'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', "
    "'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', "
    "'snowflake', 'sovrn', 'test_datastore', 'test_website', 'timescale', 'website'"
)


def upgrade():
    # Add 'aws' to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(f"create type connectiontype as enum({_NEW_VALUES})")
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove any aws connections first
    # WARNING: This permanently deletes any connectionconfig rows with connection_type='aws'.
    op.execute("delete from connectionconfig where connection_type = 'aws'")
    # Recreate enum without 'aws'
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(f"create type connectiontype as enum({_CURRENT_VALUES})")
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")
