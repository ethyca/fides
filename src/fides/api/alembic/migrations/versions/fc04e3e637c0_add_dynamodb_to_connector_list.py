"""add dynamodb to connector list

Revision ID: fc04e3e637c0
Revises: 15a3e7483249
Create Date: 2023-04-14 10:19:50.681752

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "fc04e3e637c0"
down_revision = "15a3e7483249"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'dynamodb' to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', "
        "'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', "
        "'manual_webhook', 'timescale', 'fides', 'sovrn', 'attentive', 'dynamodb')"
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
        "'email', 'manual_webhook', 'timescale', 'fides', 'sovrn', 'attentive')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
