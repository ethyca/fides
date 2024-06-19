"""scylla_connection_type

Revision ID: 3304082a6cee
Revises: a3c173391603
Create Date: 2024-06-03 19:54:20.907724

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3304082a6cee"
down_revision = "a3c173391603"
branch_labels = None
depends_on = None


def upgrade():
    # Add to ConnectionType enum
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


def downgrade():
    # Remove 'scylla' from ConnectionType
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'manual_webhook', 'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb', 'postgres', 'generic_consent_email', 'generic_erasure_email')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
