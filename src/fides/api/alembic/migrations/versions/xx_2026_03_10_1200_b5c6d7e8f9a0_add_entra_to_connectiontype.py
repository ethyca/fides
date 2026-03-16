"""Add entra to ConnectionType enum.

Revision ID: b5c6d7e8f9a0
Revises: ea20059aee77
Create Date: 2026-03-10

"""

import re

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "b5c6d7e8f9a0"
down_revision = "ea20059aee77"
branch_labels = None
depends_on = None

TYPE_TO_HANDLE = "entra"

# Only allow safe enum identifiers (alphanumeric, underscores, hyphens)
_SAFE_ENUM_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _validate_enum_value(value: str) -> str:
    """Validate that an enum value contains only safe characters."""
    if not _SAFE_ENUM_RE.match(value):
        raise ValueError(f"Unsafe enum value: {value!r}")
    return value


def get_enum_values():
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT unnest(enum_range(NULL::connectiontype))")
    ).fetchall()
    return [_validate_enum_value(row[0]) for row in result]


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
    # Remove 'entra' from ConnectionType enum.
    # WARNING: This permanently deletes any connectionconfig rows with connection_type='entra'.
    op.execute(
        text("DELETE FROM connectionconfig WHERE connection_type = :val").bindparams(
            val=TYPE_TO_HANDLE
        )
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
