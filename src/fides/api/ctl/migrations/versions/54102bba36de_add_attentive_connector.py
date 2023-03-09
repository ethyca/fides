"""add_attentive_connector

Revision ID: 54102bba36de
Revises: 2f6aa5fe797a
Create Date: 2023-03-09 22:08:17.480643

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "54102bba36de"
down_revision = "2f6aa5fe797a"
branch_labels = None
depends_on = None


def upgrade():
    # Add to ConnectionType enum
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

    # Rename field to something more generic
    op.alter_column(
        "privacyrequest",
        "awaiting_consent_email_send_at",
        new_column_name="awaiting_email_send_at",
    )

    # Rename awaiting_consent_email_send enum value to awaiting_email_send
    op.execute(
        "ALTER TYPE privacyrequeststatus RENAME VALUE 'awaiting_consent_email_send' TO 'awaiting_email_send'"
    )


def downgrade():
    # Remove attentive from the connectiontype enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', "
        "'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', "
        "'email', 'manual_webhook', 'timescale', 'fides', 'sovrn')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")

    # Revert field name
    op.alter_column(
        "privacyrequest",
        "awaiting_email_send_at",
        new_column_name="awaiting_consent_email_send_at",
    )

    # Revert awaiting_email_send enum value to awaiting_consent_email_send
    op.execute(
        "ALTER TYPE privacyrequeststatus RENAME VALUE 'awaiting_email_send' TO 'awaiting_consent_email_send'"
    )
