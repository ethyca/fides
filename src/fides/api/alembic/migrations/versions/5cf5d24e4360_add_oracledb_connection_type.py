"""add oracle_db connection type

Revision ID: 5cf5d24e4360
Revises: 6cfd59e7920a
Create Date: 2024-04-22 20:42:18.047270

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5cf5d24e4360"
down_revision = "6cfd59e7920a"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'dynamodb' to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', "
        "'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', "
        "'manual_webhook', 'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb', 'oracle_db')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove dynamodb from the connectiontype enum
    op.execute("delete from connectionconfig where connection_type in ('dynamodb')")
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', "
        "'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', "
        "'email', 'manual_webhook', 'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
