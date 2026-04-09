"""add_comment_parent_id

Revision ID: 1724da7ee981
Revises: b9c4d5e6f7a8
Create Date: 2026-04-08 19:01:40.083985

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1724da7ee981"
down_revision = "b9c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comment", sa.Column("parent_id", sa.String(length=255), nullable=True)
    )
    op.create_index("ix_comment_parent_id", "comment", ["parent_id"], unique=False)
    op.create_foreign_key(
        "comment_parent_id_fkey",
        "comment",
        "comment",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("comment_parent_id_fkey", "comment", type_="foreignkey")
    op.drop_index("ix_comment_parent_id", table_name="comment")
    op.drop_column("comment", "parent_id")
