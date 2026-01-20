"""add policy_v2 tables for runtime policy evaluation

Revision ID: 3df829c9729b
Revises: 627c230d9917
Create Date: 2026-01-14 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3df829c9729b"
down_revision = "627c230d9917"
branch_labels = None
depends_on = None


def upgrade():
    # Create policy_v2 table
    op.create_table(
        "policy_v2",
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
        sa.Column("fides_key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.BOOLEAN(), server_default="t", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fides_key", name="uq_policy_v2_fides_key"),
    )
    op.create_index(
        op.f("ix_policy_v2_fides_key"), "policy_v2", ["fides_key"], unique=True
    )
    op.create_index(
        op.f("ix_policy_v2_enabled"), "policy_v2", ["enabled"], unique=False
    )

    # Create policy_v2_rule table
    op.create_table(
        "policy_v2_rule",
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
        sa.Column("policy_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),  # ALLOW or DENY
        sa.Column("order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("on_denial_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["policy_id"], ["policy_v2.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_policy_v2_rule_policy_id"),
        "policy_v2_rule",
        ["policy_id"],
        unique=False,
    )

    # Create policy_v2_rule_match table
    op.create_table(
        "policy_v2_rule_match",
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
        sa.Column("rule_id", sa.String(length=255), nullable=False),
        sa.Column("match_type", sa.String(), nullable=False),  # 'key' or 'taxonomy'
        sa.Column("target_field", sa.String(), nullable=False),  # data_category, data_use, data_subject, data_use_taxonomies, data_category_taxonomies
        sa.Column("operator", sa.String(), server_default="any", nullable=False),  # 'any' or 'all'
        sa.Column("values", postgresql.JSONB(), nullable=False),  # List of keys or {taxonomy, element} objects
        sa.ForeignKeyConstraint(
            ["rule_id"], ["policy_v2_rule.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_policy_v2_rule_match_rule_id"),
        "policy_v2_rule_match",
        ["rule_id"],
        unique=False,
    )

    # Create policy_v2_rule_constraint table
    op.create_table(
        "policy_v2_rule_constraint",
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
        sa.Column("rule_id", sa.String(length=255), nullable=False),
        sa.Column("constraint_type", sa.String(), nullable=False),  # 'privacy' or 'context'
        sa.Column("configuration", postgresql.JSONB(), nullable=False),  # Constraint-specific config
        sa.ForeignKeyConstraint(
            ["rule_id"], ["policy_v2_rule.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_policy_v2_rule_constraint_rule_id"),
        "policy_v2_rule_constraint",
        ["rule_id"],
        unique=False,
    )


def downgrade():
    # Drop policy_v2_rule_constraint
    op.drop_index(
        op.f("ix_policy_v2_rule_constraint_rule_id"),
        table_name="policy_v2_rule_constraint",
    )
    op.drop_table("policy_v2_rule_constraint")

    # Drop policy_v2_rule_match
    op.drop_index(
        op.f("ix_policy_v2_rule_match_rule_id"),
        table_name="policy_v2_rule_match",
    )
    op.drop_table("policy_v2_rule_match")

    # Drop policy_v2_rule
    op.drop_index(
        op.f("ix_policy_v2_rule_policy_id"),
        table_name="policy_v2_rule",
    )
    op.drop_table("policy_v2_rule")

    # Drop policy_v2
    op.drop_index(op.f("ix_policy_v2_enabled"), table_name="policy_v2")
    op.drop_index(op.f("ix_policy_v2_fides_key"), table_name="policy_v2")
    op.drop_table("policy_v2")
