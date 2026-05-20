"""add tcf_version_hash_history table

Revision ID: 96fa22d82c26
Revises: 3a91e5d4f7b2
Create Date: 2026-05-07 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "96fa22d82c26"
down_revision = "1e00f8e12f44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tcf_version_hash_history",
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
        sa.Column(
            "privacy_experience_config_id",
            sa.String(length=255),
        ),
        sa.Column("previous_hash", sa.String(), nullable=True),
        sa.Column("current_hash", sa.String(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("trigger_source", sa.String(), nullable=False),
        sa.Column("details", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_experience_config_id"],
            ["privacyexperienceconfig.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tcf_version_hash_history_id"),
        "tcf_version_hash_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tcf_version_hash_history_privacy_experience_config_id"),
        "tcf_version_hash_history",
        ["privacy_experience_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tcf_version_hash_history_current_hash"),
        "tcf_version_hash_history",
        ["current_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tcf_version_hash_history_changed_at"),
        "tcf_version_hash_history",
        ["changed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_tcf_version_hash_history_changed_at"),
        table_name="tcf_version_hash_history",
    )
    op.drop_index(
        op.f("ix_tcf_version_hash_history_current_hash"),
        table_name="tcf_version_hash_history",
    )
    op.drop_index(
        op.f("ix_tcf_version_hash_history_privacy_experience_config_id"),
        table_name="tcf_version_hash_history",
    )
    op.drop_index(
        op.f("ix_tcf_version_hash_history_id"),
        table_name="tcf_version_hash_history",
    )
    op.drop_table("tcf_version_hash_history")
