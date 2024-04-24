"""add indexes to ctl_systems and privacydeclaration

Revision ID: 7f7c2b098f5d
Revises: 1af6950f4625
Create Date: 2023-11-21 18:52:34.508076

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7f7c2b098f5d"
down_revision = "1af6950f4625"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.create_index(
        "ix_ctl_systems_name",
        "ctl_systems",
        [sa.text("name gin_trgm_ops")],
        postgresql_using="gin",
    )


def downgrade():
    op.drop_index("ix_ctl_systems_name", table_name="ctl_systems")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
