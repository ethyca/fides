"""Add sovrn consent connector

Revision ID: 8e198eb13802
Revises: 643249f65453
Create Date: 2023-01-27 21:58:23.344582

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8e198eb13802"
down_revision = "643249f65453"
branch_labels = None
depends_on = None
import sqlalchemy as sa


def upgrade():
    # Add to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'email', 'manual_webhook', 'timescale', 'fides', 'sovrn')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")

    # Add new PrivacyRequest.awaiting_consent_email_send_at column
    op.add_column(
        "privacyrequest",
        sa.Column(
            "awaiting_consent_email_send_at", sa.DateTime(timezone=True), nullable=True
        ),
    )

    # Add ljt_reader_id for sovrn
    op.execute("ALTER TYPE providedidentitytype ADD VALUE 'ljt_readerID'")

    # Add new privacyrequeststatus
    op.execute(
        "alter type privacyrequeststatus add value 'awaiting_consent_email_send'"
    )


def downgrade():
    # Remove sovrn from the connectiontype enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'email', 'manual_webhook', 'timescale', 'fides')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")

    # # Drop PrivacyRequest.awaiting_consent_email_send_at column
    op.drop_column("privacyrequest", "awaiting_consent_email_send_at")

    # Remove ljt_reader_id from the providedidentitytype enum
    op.execute("ALTER TYPE providedidentitytype RENAME TO providedidentitytype_old")
    op.execute(
        "CREATE TYPE providedidentitytype AS ENUM('email', 'phone_number', 'ga_client_id')"
    )
    op.execute(
        "ALTER TABLE providedidentity ALTER COLUMN field_name TYPE providedidentitytype USING field_name::text::providedidentitytype"
    )
    op.execute("DROP TYPE providedidentitytype_old")

    # Removing awaiting_consent_email_send privacyrequeststatus
    op.execute(
        "delete from privacyrequest where status in ('awaiting_consent_email_send')"
    )
    op.execute("alter type privacyrequeststatus rename to privacyrequeststatus_old")
    op.execute(
        "create type privacyrequeststatus as enum('in_processing', 'complete', 'pending', 'error', 'paused', 'approved', 'denied', 'canceled', 'identity_unverified', 'requires_input')"
    )
    op.execute(
        (
            "alter table privacyrequest alter column status type privacyrequeststatus using "
            "status::text::privacyrequeststatus"
        )
    )
    op.execute("drop type privacyrequeststatus_old")
