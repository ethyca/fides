"""adding identity definition model

Revision ID: 67f0f2f4748e
Revises: 5093e92e2a5a
Create Date: 2025-10-27 18:34:38.326608

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "67f0f2f4748e"
down_revision = "5093e92e2a5a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "identity_definition",
        sa.Column("id", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("identity_key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("identity_key"),
    )


def downgrade():
    op.drop_table("identity_definition")
