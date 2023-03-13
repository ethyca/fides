"""add viewer role

Revision ID: 064dd27a6d41
Revises: 68a518a3c050
Create Date: 2023-03-13 23:05:38.083803

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = "064dd27a6d41"
down_revision = "68a518a3c050"
branch_labels = None
depends_on = None


def upgrade():
    """Automatic data migration: Set user scopes to empty, and set all user roles to viewer"""
    bind = op.get_bind()
    bind.execute(
        text(
            """
            UPDATE fidesuserpermissions 
            SET scopes = '{}', 
                roles = '{viewer}';
        """
        )
    )

    """Automatic data migration: Similarly Update all client scopes attached to users"""
    bind.execute(
        text(
            """
                UPDATE client 
                SET scopes = '{}', 
                    roles = '{viewer}'
                FROM fidesuserpermissions
                WHERE fidesuserpermissions.user_id = client.user_id;
            """
        )
    )


def downgrade():
    """Reverse data migration is a no-op"""
