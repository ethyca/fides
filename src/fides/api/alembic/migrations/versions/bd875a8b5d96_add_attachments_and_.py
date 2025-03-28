"""Add Attachment and AttachmentReference tables

Revision ID: bd875a8b5d96
Revises: 82883b0df5e4
Create Date: 2025-02-19 14:09:07.124680

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bd875a8b5d96"
down_revision = "82883b0df5e4"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # create attachment table
    op.create_table(
        "attachment",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("attachment_type", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["fidesuser.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_attachment_id"), "attachment", ["id"], unique=False)

    # create attachment_reference table
    op.create_table(
        "attachment_reference",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column("attachment_id", sa.String(), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=False),
        sa.Column("reference_type", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attachment_id"],
            ["attachment.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_attachment_reference_id"),
        "attachment_reference",
        ["id"],
        unique=False,
    )
    op.create_unique_constraint(
        "_attachment_reference_uc",
        "attachment_reference",
        ["attachment_id", "reference_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_attachment_reference_id"), table_name="attachment_reference")
    op.drop_table("attachment_reference")
    op.drop_index(op.f("ix_attachment_id"), table_name="attachment")
    op.drop_table("attachment")
    # ### end Alembic commands ###
