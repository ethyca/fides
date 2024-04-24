"""add saas config to connection config

Revision ID: 1dfc5a2d30e7
Revises: e55a51b354e3
Create Date: 2022-02-09 23:27:24.742938

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1dfc5a2d30e7"
down_revision = "e55a51b354e3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "connectionconfig",
        sa.Column(
            "saas_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    op.execute("alter type connectiontype rename to connectiontype_old")
    op.execute(
        "create type connectiontype as enum('postgres', 'mongodb', 'mysql', 'https', 'snowflake', 'redshift', 'mssql', 'mariadb', 'saas')"
    )
    op.execute(
        (
            "alter table connectionconfig alter column connection_type type connectiontype using "
            "connection_type::text::connectiontype"
        )
    )
    op.execute("drop type connectiontype_old")


def downgrade():
    op.drop_column("connectionconfig", "saas_config")
    op.execute("delete from connectionconfig where connection_type in ('saas')")
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
