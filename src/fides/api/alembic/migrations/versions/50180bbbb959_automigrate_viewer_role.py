"""automigrate viewer role

Revision ID: 50180bbbb959
Revises: 68a518a3c050
Create Date: 2023-03-14 14:26:32.910570

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = "50180bbbb959"
down_revision = "68a518a3c050"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "messagingconfig_service_type_key", "messagingconfig", type_="unique"
    )
    op.create_index(
        op.f("ix_messagingconfig_service_type"),
        "messagingconfig",
        ["service_type"],
        unique=True,
    )

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
    op.drop_index(op.f("ix_messagingconfig_service_type"), table_name="messagingconfig")
    op.create_unique_constraint(
        "messagingconfig_service_type_key", "messagingconfig", ["service_type"]
    )
