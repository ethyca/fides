"""add access_policy and access_policy_version tables

Revision ID: a8f3b2c1d5e7
Revises: a7b8c9d0e1f2
Create Date: 2026-03-26 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a8f3b2c1d5e7"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plus_access_policy",
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
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plus_access_policy_id", "plus_access_policy", ["id"])

    op.create_table(
        "plus_access_policy_version",
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
        sa.Column("access_policy_id", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("yaml", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["access_policy_id"],
            ["plus_access_policy.id"],
            name="plus_access_policy_version_policy_id_fkey",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_plus_access_policy_version_id", "plus_access_policy_version", ["id"]
    )
    op.create_index(
        "ix_plus_access_policy_version_policy_version",
        "plus_access_policy_version",
        ["access_policy_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_plus_access_policy_version_policy_version",
        table_name="plus_access_policy_version",
    )
    op.drop_index(
        "ix_plus_access_policy_version_id", table_name="plus_access_policy_version"
    )
    op.drop_table("plus_access_policy_version")
    op.drop_index("ix_plus_access_policy_id", table_name="plus_access_policy")
    op.drop_table("plus_access_policy")
