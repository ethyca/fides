"""add redshift and snowflake support

Revision ID: f206d4e7574d
Revises: 0210948a8147
Create Date: 2021-11-09 20:41:39.287326

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f206d4e7574d"
down_revision = "0210948a8147"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'redshift', 'snowflake')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    op.execute(
        "delete from connectionconfig where connection_type in ('snowflake', 'redshift')"
    )
    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")
