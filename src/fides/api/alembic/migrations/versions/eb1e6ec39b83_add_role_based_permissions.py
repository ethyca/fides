"""add role based permissions

Revision ID: eb1e6ec39b83
Revises: d65bbc647083
Create Date: 2023-02-24 19:27:17.844231

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy.dialects import postgresql

revision = "eb1e6ec39b83"
down_revision = "d65bbc647083"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "client",
        sa.Column("roles", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
    )
    op.add_column(
        "fidesuserpermissions",
        sa.Column("roles", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
    )
    op.alter_column(
        "fidesuserpermissions",
        "scopes",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=False,
        server_default="{}",
    )
    op.alter_column(
        "client",
        "scopes",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=False,
        server_default="{}",
    )


def downgrade():
    op.drop_column("fidesuserpermissions", "roles")
    op.drop_column("client", "roles")

    op.alter_column(
        "fidesuserpermissions",
        "scopes",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=False,
        server_default=None,
    )

    op.alter_column(
        "client",
        "scopes",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=False,
        server_default=None,
    )
