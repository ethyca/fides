"""manual webhooks

Revision ID: 7a4f4042091e
Revises: d8df7ff7aab4
Create Date: 2022-09-07 14:10:28.106679

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7a4f4042091e"
down_revision = "d8df7ff7aab4"
branch_labels = None
depends_on = None


def upgrade():
    # Add new table: AccessManualWebhook
    op.create_table(
        "accessmanualwebhook",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.Column("fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_config_id"],
            ["connectionconfig.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_config_id"),
    )
    op.create_index(
        op.f("ix_accessmanualwebhook_id"), "accessmanualwebhook", ["id"], unique=False
    )

    # Add to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'email', 'manual_webhook')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")

    # Add to PrivacyRequestStatus enum
    op.execute("alter type privacyrequeststatus add value 'requires_input'")


def downgrade():
    # Remove AccessManualWebhook table
    op.drop_index(op.f("ix_accessmanualwebhook_id"), table_name="accessmanualwebhook")
    op.drop_table("accessmanualwebhook")

    # Remove 'manual_webhook' from ConnectionType
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'email')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")

    # Remove PrivacyRequestStatus enum: requires_input
    op.execute("alter type privacyrequeststatus rename to privacyrequeststatus_old")
    op.execute(
        "create type privacyrequeststatus as enum('in_processing', 'complete', 'pending', 'error', 'paused', 'approved', 'denied', 'canceled', 'identity_unverified')"
    )
    op.execute(
        (
            "alter table privacyrequest alter column status type privacyrequeststatus using "
            "status::text::privacyrequeststatus"
        )
    )
    op.execute("drop type privacyrequeststatus_old")
