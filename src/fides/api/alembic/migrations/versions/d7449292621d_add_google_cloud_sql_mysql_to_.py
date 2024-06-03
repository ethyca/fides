"""add google_cloud_mysql to connectiontype

Revision ID: d7449292621d
Revises: 4b2eade4353c
Create Date: 2024-06-03 17:29:38.233347

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd7449292621d'
down_revision = '4b2eade4353c'
branch_labels = None
depends_on = None



def upgrade():
    # Add google_cloud_mysql to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual', 'email', 'manual_webhook', 'timescale', 'fides', 'sovrn', 'google_cloud_mysql')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")



def downgrade():
    # Remove google_cloud_mysql from the ConnectionType enum
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
