"""add property config and css

Revision ID: 0debabbb9c6a
Revises: 4fba24045fec
Create Date: 2024-05-06 16:45:45.958888

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0debabbb9c6a"
down_revision = "4fba24045fec"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "plus_property",
        sa.Column(
            "privacy_center_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column("plus_property", sa.Column("stylesheet", sa.Text(), nullable=True))
    op.add_column(
        "plus_property",
        sa.Column("paths", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
    )


def downgrade():
    op.drop_column("plus_property", "paths")
    op.drop_column("plus_property", "stylesheet")
    op.drop_column("plus_property", "privacy_center_config")
