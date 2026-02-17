"""Add jira_ticket to ConnectionType enum

Revision ID: cc9a5690f9e7
Revises: c0dc13ad2a05
Create Date: 2026-02-13 12:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "cc9a5690f9e7"
down_revision = "c0dc13ad2a05"
branch_labels = None
depends_on = None

# Current enum values (before this migration)
_CURRENT_VALUES = (
    "'attentive_email', 'bigquery', 'datahub', 'dynamodb', 'fides', "
    "'generic_consent_email', 'generic_erasure_email', 'dynamic_erasure_email', "
    "'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', "
    "'manual', 'manual_webhook', 'manual_task', "
    "'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', "
    "'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', "
    "'snowflake', 'sovrn', 'test_datastore', 'test_website', 'timescale', 'website'"
)

# New enum values (after this migration)
_NEW_VALUES = (
    "'attentive_email', 'bigquery', 'datahub', 'dynamodb', 'fides', "
    "'generic_consent_email', 'generic_erasure_email', 'dynamic_erasure_email', "
    "'google_cloud_sql_mysql', 'google_cloud_sql_postgres', 'https', "
    "'jira_ticket', "
    "'manual', 'manual_webhook', 'manual_task', "
    "'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', "
    "'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', "
    "'snowflake', 'sovrn', 'test_datastore', 'test_website', 'timescale', 'website'"
)


def upgrade():
    # Add 'jira_ticket' to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(f"create type connectiontype as enum({_NEW_VALUES})")
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove any jira_ticket connections first
    op.execute(
        "delete from connectionconfig where connection_type = 'jira_ticket'"
    )
    # Recreate enum without 'jira_ticket'
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(f"create type connectiontype as enum({_CURRENT_VALUES})")
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")
