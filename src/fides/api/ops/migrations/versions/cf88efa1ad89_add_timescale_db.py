"""add timescale db

Revision ID: cf88efa1ad89
Revises: 021d288d0ce3
Create Date: 2022-09-14 21:26:43.721397

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cf88efa1ad89"
down_revision = "021d288d0ce3"
branch_labels = None
depends_on = None


def upgrade():
    # Add to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'email', 'manual_webhook', 'timescale')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove 'timescale' from ConnectionType
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
