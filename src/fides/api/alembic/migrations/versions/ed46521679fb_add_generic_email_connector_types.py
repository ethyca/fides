"""add generic email connector types

Revision ID: ed46521679fb
Revises: 587c53fe3e99
Create Date: 2023-05-19 23:25:48.711050

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ed46521679fb"
down_revision = "587c53fe3e99"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'generic_consent_email' and 'generic_erasure_email' to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('mongodb', 'mysql', 'https', 'snowflake', "
        "'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'manual_webhook', "
        "'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb', 'postgres',"
        "'generic_consent_email', 'generic_erasure_email')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove 'generic_consent_email' and 'generic_erasure_email' from ConnectionType enum
    op.execute(
        "delete from connectionconfig where connection_type in ('generic_consent_email', 'generic_erasure_email')"
    )
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('mongodb', 'mysql', 'https', 'snowflake', "
        "'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'manual_webhook', "
        "'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb', 'postgres')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
