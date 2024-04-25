"""new tables for pre-approval webhooks

Revision ID: 6cfd59e7920a
Revises: d49a767eb49d
Create Date: 2024-04-15 13:14:39.027682

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6cfd59e7920a"
down_revision = "d49a767eb49d"
branch_labels = None
depends_on = None


def upgrade():
    # Add new table: PreApprovalWebhook
    op.create_table(
        "preapprovalwebhook",
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
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_config_id"],
            ["connectionconfig.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_preapprovalwebhook_id"), "preapprovalwebhook", ["id"], unique=False
    )

    # Add new table: PreApprovalWebhookReply
    op.create_table(
        "preapprovalwebhookreply",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("webhook_id", sa.String(length=255), nullable=False),
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
        sa.Column("privacy_request_id", sa.String(), nullable=True),
        sa.Column("is_eligible", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"],
            ["privacyrequest.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_preapprovalwebhookreply_id"),
        "preapprovalwebhookreply",
        ["id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # Remove PreApprovalWebhook and PreApprovalWebhookReply tables
    op.drop_index(op.f("ix_preapprovalwebhook_id"), table_name="preapprovalwebhook")
    op.drop_index(
        op.f("ix_preapprovalwebhookreply_id"), table_name="preapprovalwebhookreply"
    )
    op.drop_table("preapprovalwebhook")
    op.drop_table("preapprovalwebhookreply")
    # ### end Alembic commands ###
