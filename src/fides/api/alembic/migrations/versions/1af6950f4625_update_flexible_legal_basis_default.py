"""update_flexible_legal_basis_default

Revision ID: 1af6950f4625
Revises: 3cc39a6ce32b
Create Date: 2023-11-15 22:15:38.688530

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy

revision = "1af6950f4625"
down_revision = "3cc39a6ce32b"
branch_labels = None
depends_on = None


def upgrade():
    bind: Connection = op.get_bind()

    bind.execute(
        text(
            """
            UPDATE privacydeclaration 
            SET flexible_legal_basis_for_processing = false 
            WHERE flexible_legal_basis_for_processing IS NULL;
            """
        )
    )

    op.alter_column(
        "privacydeclaration",
        "flexible_legal_basis_for_processing",
        existing_type=sa.BOOLEAN(),
        server_default="t",
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "privacydeclaration",
        "flexible_legal_basis_for_processing",
        existing_type=sa.BOOLEAN(),
        nullable=True,
        server_default=None,
    )
