"""index preference created and updated

Revision ID: 8342453518cc
Revises: 144d9b85c712
Create Date: 2023-04-19 18:33:17.034245

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8342453518cc"
down_revision = "144d9b85c712"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        op.f("ix_currentprivacypreference_created_at"),
        "currentprivacypreference",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_updated_at"),
        "currentprivacypreference",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_created_at"),
        "privacypreferencehistory",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacypreferencehistory_created_at"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_updated_at"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_created_at"),
        table_name="currentprivacypreference",
    )
