"""add google_cloud_sql_mysql to connectiontype

Revision ID: 98e0860a9320
Revises: efddde14da21
Create Date: 2024-06-05 15:32:18.414155

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98e0860a9320'
down_revision = 'efddde14da21'
branch_labels = None
depends_on = None


def upgrade():
    # Add google_cloud_sql_mysql to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'email', 'manual_webhook', 'timescale', 'fides', 'sovrn', 'google_cloud_sql_mysql')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")



def downgrade():
    # Remove google_cloud_sql_mysql from the ConnectionType enum
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
