"""add policy webhooks

Revision ID: c5336b841d70
Revises: f206d4e7574d
Create Date: 2021-11-24 23:20:48.807643

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c5336b841d70"
down_revision = "f206d4e7574d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "policypostwebhook",
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
        sa.Column("key", sa.String(), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("one_way", "two_way", name="webhookdirection"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.String(), nullable=False),
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_config_id"],
            ["connectionconfig.id"],
        ),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["policy.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_policypostwebhook_id"), "policypostwebhook", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_policypostwebhook_key"), "policypostwebhook", ["key"], unique=True
    )
    op.create_table(
        "policyprewebhook",
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
        sa.Column("key", sa.String(), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("one_way", "two_way", name="webhookdirection"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.String(), nullable=False),
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_config_id"],
            ["connectionconfig.id"],
        ),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["policy.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_policyprewebhook_id"), "policyprewebhook", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_policyprewebhook_key"), "policyprewebhook", ["key"], unique=True
    )


def downgrade():
    op.drop_index(op.f("ix_policyprewebhook_key"), table_name="policyprewebhook")
    op.drop_index(op.f("ix_policyprewebhook_id"), table_name="policyprewebhook")
    op.drop_table("policyprewebhook")
    op.drop_index(op.f("ix_policypostwebhook_key"), table_name="policypostwebhook")
    op.drop_index(op.f("ix_policypostwebhook_id"), table_name="policypostwebhook")
    op.drop_table("policypostwebhook")
