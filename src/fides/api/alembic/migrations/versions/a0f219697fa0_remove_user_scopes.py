"""remove user scopes

Revision ID: a0f219697fa0
Revises: 54102bba36de
Create Date: 2023-03-15 22:25:09.654149

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a0f219697fa0"
down_revision = "54102bba36de"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("fidesuserpermissions", "scopes")
    """One last time - remove scopes from user clients"""
    bind = op.get_bind()
    bind.execute(
        text(
            """
                UPDATE client 
                SET scopes = '{}'
                FROM fidesuserpermissions
                WHERE fidesuserpermissions.user_id = client.user_id;
            """
        )
    )


def downgrade():
    op.add_column(
        "fidesuserpermissions",
        sa.Column(
            "scopes",
            postgresql.ARRAY(sa.VARCHAR()),
            server_default=sa.text("'{}'::character varying[]"),
            autoincrement=False,
            nullable=True,
        ),
    )
