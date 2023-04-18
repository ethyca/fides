"""index privacy preference created

Revision ID: 3ac5aef6fe45
Revises: 144d9b85c712
Create Date: 2023-04-18 03:09:45.137878

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3ac5aef6fe45"
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
        op.f("ix_currentprivacypreference_created_at"),
        table_name="currentprivacypreference",
    )
