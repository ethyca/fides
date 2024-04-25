"""Added messaging template table

Revision ID: 507563f6f8d4
Revises: fd52d5f08c17
Create Date: 2023-08-05 05:30:52.105840

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "507563f6f8d4"
down_revision = "fd52d5f08c17"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "messaging_template",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_messagingtemplate_id"), "messaging_template", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_messagingtemplate_key"), "messaging_template", ["key"], unique=True
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f("ix_messagingtemplate_key"), table_name="messaging_template")
    op.drop_index(op.f("ix_messagingtemplate_id"), table_name="messaging_template")
    op.drop_table("messaging_template")
