"""make ConnectionConfig.name optional

Revision ID: 7315b9d7fda6
Revises: d2996381c4dd
Create Date: 2023-06-26 20:39:29.953904

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7315b9d7fda6"
down_revision = "d2996381c4dd"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("connectionconfig", "name", nullable=True)

    op.drop_index(op.f("ix_connectionconfig_name"), table_name="connectionconfig")


def downgrade():
    op.alter_column("connectionconfig", "name", nullable=False)

    conn = op.get_bind()
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_connectionconfig_name ON connectionconfig (name);"
    )
