"""add_manual_task_to_connectiontype_enum

Revision ID: aadfe83c5644
Revises: 6a76a1fa4f3f
Create Date: 2025-06-19 18:55:08.131278

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "aadfe83c5644"
down_revision = "6a76a1fa4f3f"
branch_labels = None
depends_on = None


def upgrade():
    # Add manual_task to ConnectionType enum
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'manual', 'mariadb', 'bigquery', 'saas', 'email', 'manual_webhook', 'manual_task')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    # Remove manual_task from ConnectionType enum
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
