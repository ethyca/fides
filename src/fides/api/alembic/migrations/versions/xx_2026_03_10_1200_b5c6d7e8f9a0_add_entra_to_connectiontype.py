"""Add entra to ConnectionType enum.

Revision ID: b5c6d7e8f9a0
Revises: baa6792fc3f7
Create Date: 2026-03-10

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b5c6d7e8f9a0"
down_revision = "baa6792fc3f7"
branch_labels = None
depends_on = None

# Current enum values (before this migration)
_CURRENT_VALUES = (
    "'attentive_email', 'bigquery', 'datahub', 'dynamic_erasure_email', 'dynamodb', "
    "'fides', 'generic_consent_email', 'generic_erasure_email', "
    "'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', "
    "'jira_ticket', 'manual', 'manual_task', 'manual_webhook', "
    "'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', "
    "'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', "
    "'snowflake', 'sovrn', 'test_datastore', 'test_website', 'timescale', 'website'"
)

# New enum values (after this migration)
_NEW_VALUES = (
    "'attentive_email', 'bigquery', 'datahub', 'dynamic_erasure_email', 'dynamodb', "
    "'entra', 'fides', 'generic_consent_email', 'generic_erasure_email', "
    "'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', "
    "'jira_ticket', 'manual', 'manual_task', 'manual_webhook', "
    "'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', "
    "'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', "
    "'snowflake', 'sovrn', 'test_datastore', 'test_website', 'timescale', 'website'"
)


def upgrade():
    # Add 'entra' to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(f"create type connectiontype as enum({_NEW_VALUES})")
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove any entra connections first
    # WARNING: This permanently deletes any connectionconfig rows with connection_type='entra'.
    op.execute("delete from connectionconfig where connection_type = 'entra'")
    # Recreate enum without 'entra'
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(f"create type connectiontype as enum({_CURRENT_VALUES})")
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")
