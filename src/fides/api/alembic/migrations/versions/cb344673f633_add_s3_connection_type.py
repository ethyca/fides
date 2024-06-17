"""add s3 connection type

Revision ID: cb344673f633
Revises: 3304082a6cee
Create Date: 2024-05-31 20:46:08.829330

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cb344673f633"
down_revision = "3304082a6cee"
branch_labels = None
depends_on = None


def upgrade():
    # Add 's3' to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'manual_webhook', 'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb', 'postgres', 'generic_consent_email', 'generic_erasure_email', 'scylla', 's3')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove 's3' from ConnectionType enum
    op.execute("delete from connectionconfig where connection_type in ('s3')")
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'manual_webhook', 'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb', 'postgres', 'generic_consent_email', 'generic_erasure_email', 'scylla')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
