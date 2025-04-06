"""Add comments and comment references

Revision ID: 69ad6d844e21
Revises: 6ea2171c544f
Create Date: 2025-03-03 16:31:22.495305

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "69ad6d844e21"
down_revision = "6ea2171c544f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "comment",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("comment_text", sa.String(), nullable=False),
        sa.Column("comment_type", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["fidesuser.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "comment_reference",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("comment_id", sa.String(), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=False),
        sa.Column("reference_type", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["comment_id"], ["comment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comment_id", "reference_id"),
    )
    # Add index on comment_reference.reference_id
    op.create_index(
        "ix_comment_reference_reference_id",
        "comment_reference",
        ["reference_id"],
    )
    # Add index on comment_reference.reference_type
    op.create_index(
        "ix_comment_reference_reference_type",
        "comment_reference",
        ["reference_type"],
    )
    # ### end Alembic commands ###


def downgrade():
    # Drop the index on comment_reference.reference_id
    op.drop_index("ix_comment_reference_reference_id", table_name="comment_reference")
    # Drop the index on comment_reference.reference_type
    op.drop_index("ix_comment_reference_reference_type", table_name="comment_reference")
    op.drop_table("comment_reference")
    op.drop_table("comment")
    # ### end Alembic commands ###
