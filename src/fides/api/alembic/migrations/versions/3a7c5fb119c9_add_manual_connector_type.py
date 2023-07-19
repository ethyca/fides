"""add manual connector type, and add "paused" status to execution logs

Revision ID: 3a7c5fb119c9
Revises: 5078badb90b9
Create Date: 2022-05-13 19:18:45.400669

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3a7c5fb119c9"
down_revision = "5078badb90b9"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas', 'manual')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
    op.execute("alter type executionlogstatus add value 'paused'")


def downgrade():
    # Downgrade connection_type
    op.execute("delete from connectionconfig where connection_type in ('manual')")
    op.execute("delete from executionlog where status = 'paused'")

    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'bigquery', 'saas')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")

    # Downgrade executionlogstatus
    op.execute("alter type executionlogstatus rename to executionlogstatus_old")
    op.execute(
        "create type executionlogstatus as enum('in_processing', 'pending', 'complete', 'error', 'retrying')"
    )
    op.execute(
        (
            "alter table executionlog alter column status type executionlogstatus using "
            "status::text::executionlogstatus"
        )
    )
    op.execute("drop type executionlogstatus_old")
