"""add authorization request

Revision ID: 1ff88b7bd579
Revises: 3a7c5fb119c9
Create Date: 2022-05-25 04:09:22.149110

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1ff88b7bd579"
down_revision = "3a7c5fb119c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "authenticationrequest",
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
        sa.Column("connection_key", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_key"),
    )
    op.create_index(
        op.f("ix_authenticationrequest_id"),
        "authenticationrequest",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_authenticationrequest_state"),
        "authenticationrequest",
        ["state"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f("ix_authenticationrequest_state"), table_name="authenticationrequest"
    )
    op.drop_index(
        op.f("ix_authenticationrequest_id"), table_name="authenticationrequest"
    )
    op.drop_table("authenticationrequest")
