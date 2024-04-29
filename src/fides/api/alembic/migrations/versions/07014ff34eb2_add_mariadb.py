"""add mariadb

Revision ID: 07014ff34eb2
Revises: f3841942d90c
Create Date: 2022-01-27 19:18:11.899734

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "07014ff34eb2"
down_revision = "f3841942d90c"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    op.execute("delete from connectionconfig where connection_type in ('mariadb')")
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
