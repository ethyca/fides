"""add policy conditions

Revision ID: 6d5f70dd0ba5
Revises: 627c230d9917
Create Date: 2025-12-09 12:36:02.092314

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6d5f70dd0ba5"
down_revision = "627c230d9917"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "policy_condition",
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
            "condition_tree",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("policy_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policy.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_id", name="uq_policy_condition_policy_id"),
    )
    op.create_index(
        op.f("ix_policy_condition_policy_id"),
        "policy_condition",
        ["policy_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_policy_condition_policy_id"), table_name="policy_condition")
    op.drop_table("policy_condition")
