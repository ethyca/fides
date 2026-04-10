"""Add google_workspace to ConnectionType

Revision ID: b3c8d5e7f2a1
Revises: b9c4d5e6f7a8
Create Date: 2026-04-05 14:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b3c8d5e7f2a1"
down_revision = "b9c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum("
        "'attentive_email', 'bigquery', 'datahub', 'dynamic_erasure_email', "
        "'dynamodb', 'entra', 'fides', 'generic_consent_email', "
        "'generic_erasure_email', 'google_cloud_sql_mysql', "
        "'google_cloud_sql_postgres', 'google_workspace', 'https', "
        "'jira_ticket', 'manual', 'manual_task', 'manual_webhook', "
        "'mariadb', 'mongodb', 'mssql', 'mysql', 'okta', 'postgres', "
        "'rds_mysql', 'rds_postgres', 'redshift', 's3', 'saas', 'scylla', "
        "'snowflake', 'sovrn', 'test_datastore', 'test_website', "
        "'timescale', 'website')"
    )
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    op.execute(
        "delete from connectionconfig where connection_type = 'google_workspace'"
    )
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum("
        "'attentive_email', 'bigquery', 'datahub', 'dynamic_erasure_email', "
        "'dynamodb', 'entra', 'fides', 'generic_consent_email', "
        "'generic_erasure_email', 'google_cloud_sql_mysql', "
        "'google_cloud_sql_postgres', 'https', 'jira_ticket', 'manual', "
        "'manual_task', 'manual_webhook', 'mariadb', 'mongodb', 'mssql', "
        "'mysql', 'okta', 'postgres', 'rds_mysql', 'rds_postgres', "
        "'redshift', 's3', 'saas', 'scylla', 'snowflake', 'sovrn', "
        "'test_datastore', 'test_website', 'timescale', 'website')"
    )
    op.execute(
        "alter table connectionconfig alter column connection_type "
        "type connectiontype using connection_type::text::connectiontype"
    )
    op.execute("drop type connectiontype_old")
