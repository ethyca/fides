"""add okta to connection_types

Revision ID: d0cbfec0b2dd
Revises: c9c72b3d550b
Create Date: 2025-04-23 15:22:57.920715

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d0cbfec0b2dd"
down_revision = "c9c72b3d550b"
branch_labels = None
depends_on = None

type_to_handle = "okta"


def get_enum_values():
    conn = op.get_bind()
    result = conn.execute("SELECT unnest(enum_range(NULL::connectiontype))").fetchall()
    return [row[0] for row in result]


def upgrade():
    # add 'okta' to ConnectionType enum
    enum_values = [f"'{value}'" for value in get_enum_values() + [type_to_handle]]
    enum_values.sort()  # Just to keep it fantastic

    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")
    op.execute(f"CREATE TYPE connectiontype AS ENUM ({', '.join(set(enum_values))})")
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_old")


def downgrade():
    # Remove 'okta' from ConnectionType enum
    enum_values = [f"'{v.strip()}'" for v in get_enum_values() if v != type_to_handle]
    enum_values.sort()  # Just to keep it fantastic

    op.execute(
        f"DELETE FROM connectionconfig WHERE connection_type IN ('{type_to_handle}')"
    )
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")

    op.execute(f"CREATE TYPE connectiontype AS ENUM ({', '.join(set(enum_values))})")
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_old")
