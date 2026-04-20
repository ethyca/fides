"""add attachment_user_provided

Revision ID: 9b449105864d
Revises: d6e7f8a9b0c1
Create Date: 2026-04-17 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9b449105864d"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attachment_user_provided",
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
            nullable=False,
        ),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "promoted",
                "deleted",
                name="attachmentuserprovidedstatus",
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "object_key", name="uq_attachment_user_provided_object_key"
        ),
    )
    op.create_index(
        op.f("ix_attachment_user_provided_id"),
        "attachment_user_provided",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_attachment_user_provided_status_created_at",
        "attachment_user_provided",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_attachment_user_provided_status_created_at",
        table_name="attachment_user_provided",
    )
    op.drop_index(
        op.f("ix_attachment_user_provided_id"),
        table_name="attachment_user_provided",
    )
    op.drop_table("attachment_user_provided")
    op.execute("DROP TYPE attachmentuserprovidedstatus")
