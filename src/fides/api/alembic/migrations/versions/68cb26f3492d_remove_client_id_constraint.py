"""remove client id constraint

Revision ID: 68cb26f3492d
Revises: 956d21f13def
Create Date: 2024-02-01 18:07:16.757838

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "68cb26f3492d"
down_revision = "956d21f13def"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("policy", "client_id", existing_type=sa.VARCHAR(), nullable=True)


def downgrade():
    op.alter_column("policy", "client_id", existing_type=sa.VARCHAR(), nullable=False)
