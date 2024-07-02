"""pre_approval_webhook_cleanup

Revision ID: 9e83545ed9b6
Revises: c85a641cc92c
Create Date: 2024-04-26 23:47:27.821607

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9e83545ed9b6"
down_revision = "c85a641cc92c"
branch_labels = None
depends_on = None


def upgrade():
    # Index PreApproval Webhook Key
    op.create_index(
        op.f("ix_preapprovalwebhook_key"), "preapprovalwebhook", ["key"], unique=True
    )
    # Create Unique Constraint on Preapproval Webhook Name
    op.create_unique_constraint(
        "preapprovalwebhook_name_key", "preapprovalwebhook", ["name"]
    )
    # Remove PreApprovalWebhook.connection_config_id FK
    op.drop_constraint(
        "preapprovalwebhook_connection_config_id_fkey",
        "preapprovalwebhook",
        type_="foreignkey",
    )
    # Restore PreApprovalWebhook.connection_config_id FK with cascade delete
    op.create_foreign_key(
        "preapprovalwebhook_connection_config_id_fkey",
        "preapprovalwebhook",
        "connectionconfig",
        ["connection_config_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Set Preapproval Webhook Reply to nullable in case the Webhook is deleted
    op.alter_column(
        "preapprovalwebhookreply",
        "webhook_id",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )
    # Index the PreApprovalWebhookReply.privacy_request_id
    op.create_index(
        op.f("ix_preapprovalwebhookreply_privacy_request_id"),
        "preapprovalwebhookreply",
        ["privacy_request_id"],
        unique=False,
    )
    # Index the PreApprovalWebhookReply.webhook_id
    op.create_index(
        op.f("ix_preapprovalwebhookreply_webhook_id"),
        "preapprovalwebhookreply",
        ["webhook_id"],
        unique=False,
    )
    # Remove FK on preapprovalwebhookreply.privacy_request_id
    op.drop_constraint(
        "preapprovalwebhookreply_privacy_request_id_fkey",
        "preapprovalwebhookreply",
        type_="foreignkey",
    )
    # Add FK on preapprovalwebhookreply.webhook_id with ondelete set null
    op.create_foreign_key(
        "preapprovalwebhookreply_webhook_id_fkey",
        "preapprovalwebhookreply",
        "preapprovalwebhook",
        ["webhook_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Restore FK on preapprovalwebhookreply.privacy_request_id with ondelete set null
    op.create_foreign_key(
        "preapprovalwebhookreply_privacy_request_id_fkey",
        "preapprovalwebhookreply",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "preapprovalwebhookreply_privacy_request_id_fkey",
        "preapprovalwebhookreply",
        type_="foreignkey",
    )
    op.drop_constraint(
        "preapprovalwebhookreply_webhook_id_fkey",
        "preapprovalwebhookreply",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "preapprovalwebhookreply_privacy_request_id_fkey",
        "preapprovalwebhookreply",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
    )
    op.drop_index(
        op.f("ix_preapprovalwebhookreply_webhook_id"),
        table_name="preapprovalwebhookreply",
    )
    op.drop_index(
        op.f("ix_preapprovalwebhookreply_privacy_request_id"),
        table_name="preapprovalwebhookreply",
    )
    op.drop_constraint(
        "preapprovalwebhook_connection_config_id_fkey",
        "preapprovalwebhook",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "preapprovalwebhook_connection_config_id_fkey",
        "preapprovalwebhook",
        "connectionconfig",
        ["connection_config_id"],
        ["id"],
    )
    op.drop_constraint(
        "preapprovalwebhook_name_key", "preapprovalwebhook", type_="unique"
    )
    op.drop_index(op.f("ix_preapprovalwebhook_key"), table_name="preapprovalwebhook")
