"""create digest conditional dependencies

Revision ID: 918aefc950c9
Revises: e2cda8d6abc3
Create Date: 2025-09-18 21:04:23.620675

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "918aefc950c9"
down_revision = "e2cda8d6abc3"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "digest_condition",
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
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("digest_config_id", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.String(length=255), nullable=True),
        sa.Column("digest_condition_type", sa.String(), nullable=False),
        sa.Column("condition_type", sa.String(), nullable=False),
        sa.Column("field_address", sa.String(length=255), nullable=True),
        sa.Column("operator", sa.String(), nullable=True),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("logical_operator", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["digest_config_id"], ["digest_config.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["digest_condition.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_digest_condition_condition_type",
        "digest_condition",
        ["condition_type"],
        unique=False,
    )
    op.create_index(
        "ix_digest_condition_digest_condition_type",
        "digest_condition",
        ["digest_condition_type"],
        unique=False,
    )
    op.create_index(
        "ix_digest_condition_digest_config_id",
        "digest_condition",
        ["digest_config_id"],
        unique=False,
    )
    op.create_index(
        "ix_digest_condition_parent_id",
        "digest_condition",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        "ix_digest_condition_sort_order",
        "digest_condition",
        ["sort_order"],
        unique=False,
    )

    # Unique constraint to ensure only one root condition per digest_condition_type per digest_config
    op.create_index(
        "ix_digest_condition_unique_root_per_type",
        "digest_condition",
        ["digest_config_id", "digest_condition_type"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )
    # ### end Alembic commands ###


def downgrade():

    op.drop_index(
        "ix_digest_condition_unique_root_per_type",
        table_name="digest_condition",
    )
    op.drop_index(
        "ix_digest_condition_sort_order",
        table_name="digest_condition",
    )
    op.drop_index(
        "ix_digest_condition_parent_id",
        table_name="digest_condition",
    )
    op.drop_index(
        "ix_digest_condition_digest_config_id",
        table_name="digest_condition",
    )
    op.drop_index(
        "ix_digest_condition_digest_condition_type",
        table_name="digest_condition",
    )
    op.drop_index(
        "ix_digest_condition_condition_type",
        table_name="digest_condition",
    )

    op.drop_table("digest_condition")
    # ### end Alembic commands ###
