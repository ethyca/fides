"""add aws connection type

Revision ID: c8ebcf66132a
Revises: a1ca9ddf3c3c
Create Date: 2026-03-17 14:14:15.346395

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c8ebcf66132a"
down_revision = "a1ca9ddf3c3c"
branch_labels = None
depends_on = None

# Enum values before this migration
_VALUES = [
    "attentive_email", "bigquery", "datahub", "dynamic_erasure_email", "dynamodb",
    "entra", "fides", "generic_consent_email", "generic_erasure_email",
    "google_cloud_sql_mysql", "google_cloud_sql_postgres", "https",
    "jira_ticket", "manual", "manual_task", "manual_webhook",
    "mariadb", "mongodb", "mssql", "mysql", "okta", "postgres",
    "rds_mysql", "rds_postgres", "redshift", "s3", "saas", "scylla",
    "snowflake", "sovrn", "test_datastore", "test_website", "timescale", "website",
]


def _as_enum(values):
    return ", ".join(f"'{v}'" for v in values)


def upgrade():
    # Add 'aws' to ConnectionType enum
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")
    op.execute(f"CREATE TYPE connectiontype AS ENUM({_as_enum(sorted(_VALUES + ['aws']))})")
    op.execute(
        "ALTER TABLE connectionconfig ALTER COLUMN connection_type "
        "TYPE connectiontype USING connection_type::text::connectiontype"
    )
    op.execute("DROP TYPE connectiontype_old")


def downgrade():
    # Remove any aws connections first
    op.execute("DELETE FROM connectionconfig WHERE connection_type = 'aws'")
    # Recreate enum without 'aws'
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")
    op.execute(f"CREATE TYPE connectiontype AS ENUM({_as_enum(_VALUES)})")
    op.execute(
        "ALTER TABLE connectionconfig ALTER COLUMN connection_type "
        "TYPE connectiontype USING connection_type::text::connectiontype"
    )
    op.execute("DROP TYPE connectiontype_old")
