"""add okta to connection_types

Revision ID: d0cbfec0b2dd
Revises: c9c72b3d550b
Create Date: 2025-04-23 15:22:57.920715

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd0cbfec0b2dd'
down_revision = 'c9c72b3d550b'
branch_labels = None
depends_on = None

type_to_handle = "okta"

def upgrade():
    # add 'okta' to ConnectionType enum
    conn = op.get_bind()
    result = conn.execute("SELECT enum_range(NULL::connectiontype)").scalar()
    current_values = result[1:-1].split(',')  # Remove the {} and split by comma
    enum_values = [f"'{v.strip()}'" for v in current_values + [type_to_handle]]
    enum_values.sort()  # Just to keep it fantastic
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
    # Remove 'okta' from ConnectionType enum
    conn = op.get_bind()
    result = conn.execute("SELECT enum_range(NULL::connectiontype)").scalar()
    current_values = result[1:-1].split(',')  # Remove the {} and split by comma
    enum_values = [f"'{v.strip()}'" for v in current_values if v.strip() != type_to_handle]
    enum_values.sort()  # Just to keep it fantastic

    op.execute(f"DELETE FROM connectionconfig WHERE connection_type IN ('{type_to_handle}')")
    op.execute("ALTER TYPE connectiontype RENAME TO connectiontype_old")

    op.execute(f"CREATE TYPE connectiontype AS ENUM ({', '.join(enum_values)})")
    op.execute(
        """
        ALTER TABLE connectionconfig ALTER COLUMN connection_type TYPE connectiontype USING
        connection_type::text::connectiontype
    """
    )
    op.execute("DROP TYPE connectiontype_old")
