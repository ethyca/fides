"""Add entra to ConnectionType enum.

Revision ID: b5c6d7e8f9a0
Revises: 074796d61d8a
Create Date: 2026-03-10

"""

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "b5c6d7e8f9a0"
down_revision = "074796d61d8a"
branch_labels = None
depends_on = None

TYPE_TO_HANDLE = "entra"


def get_enum_values():
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT unnest(enum_range(NULL::connectiontype))")
    ).fetchall()
    return [row[0] for row in result]


def upgrade():
    # Add 'entra' to ConnectionType enum
    enum_values = sorted(
        set(f"'{value}'" for value in get_enum_values() + [TYPE_TO_HANDLE])
    )

    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")
    op.execute(f"CREATE TYPE connectiontype AS ENUM ({', '.join(enum_values)})")
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_old")


def downgrade():
    # Remove 'entra' from ConnectionType enum
    op.execute(
        f"DELETE FROM connectionconfig WHERE connection_type IN ('{TYPE_TO_HANDLE}')"
    )
    enum_values = sorted(
        set(f"'{v}'" for v in get_enum_values() if v != TYPE_TO_HANDLE)
    )

    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")
    op.execute(f"CREATE TYPE connectiontype AS ENUM ({', '.join(enum_values)})")
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_old")
