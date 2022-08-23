"""add connection config description

Revision ID: b3b68c87c4a0
Revises: c3472d75c80e
Create Date: 2022-06-13 17:24:56.889227

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3b68c87c4a0"
down_revision = "c3472d75c80e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "connectionconfig", sa.Column("description", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_connectionconfig_description"),
        "connectionconfig",
        ["description"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_connectionconfig_description"), table_name="connectionconfig"
    )
    op.drop_column("connectionconfig", "description")
