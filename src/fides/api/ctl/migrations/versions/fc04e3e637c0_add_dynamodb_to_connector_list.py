"""add dynamodb to connector list

Revision ID: fc04e3e637c0
Revises: ff782b0dc07e
Create Date: 2023-04-14 10:19:50.681752

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fc04e3e637c0"
down_revision = "ff782b0dc07e"
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

    # Rename field to something more generic
    # op.alter_column(
    #     "privacyrequest",
    #     "awaiting_consent_email_send_at",
    #     new_column_name="awaiting_email_send_at",
    # )

    # Rename awaiting_consent_email_send enum value to awaiting_email_send
    # op.execute(
    #     "ALTER TYPE privacyrequeststatus RENAME VALUE 'awaiting_consent_email_send' TO 'awaiting_email_send'"
    # )


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

    # Revert field name
    # op.alter_column(
    #     "privacyrequest",
    #     "awaiting_email_send_at",
    #     new_column_name="awaiting_consent_email_send_at",
    # )

    # # Revert awaiting_email_send enum value to awaiting_consent_email_send
    # op.execute(
    #     "ALTER TYPE privacyrequeststatus RENAME VALUE 'awaiting_email_send' TO 'awaiting_consent_email_send'"
    # )
