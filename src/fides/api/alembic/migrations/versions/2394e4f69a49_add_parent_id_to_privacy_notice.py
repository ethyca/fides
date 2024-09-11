"""add parent ID to privacy notice

Revision ID: 2394e4f69a49
Revises: 9de4bb76307a
Create Date: 2024-09-09 21:28:20.286331

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2394e4f69a49"
down_revision = "9de4bb76307a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("privacynotice", sa.Column("parent_id", sa.String(), nullable=True))
    op.create_foreign_key(
        None,
        "privacynotice",
        "privacynotice",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(None, "privacynotice", type_="foreignkey")
    op.drop_column("privacynotice", "parent_id")
