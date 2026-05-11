"""Add Postgres columns/tables for DSR pipeline state (Redis cutover).

Revision ID: b8c4d2e1f3a5
Revises: 3a91e5d4f7b2
Create Date: 2026-05-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from fides.api.db.encryption_utils import encrypted_type
from fides.api.db.base_class import JSONTypeOverride

# revision identifiers, used by Alembic.
revision = "b8c4d2e1f3a5"
down_revision = "3a91e5d4f7b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "privacyrequest",
        sa.Column("encryption_key", encrypted_type(sa.String), nullable=True),
    )
    op.add_column(
        "privacyrequest",
        sa.Column("drp_request_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "data_use_map",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column("privacyrequest", sa.Column("paused_step", sa.String(), nullable=True))
    op.add_column(
        "privacyrequest", sa.Column("paused_collection", sa.String(), nullable=True)
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "paused_action_needed",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column("privacyrequest", sa.Column("failed_step", sa.String(), nullable=True))
    op.add_column(
        "privacyrequest", sa.Column("failed_collection", sa.String(), nullable=True)
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "failed_action_needed",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column("privacyrequest", sa.Column("celery_task_id", sa.String(), nullable=True))
    op.create_index(
        "ix_privacyrequest_celery_task_id",
        "privacyrequest",
        ["celery_task_id"],
        unique=False,
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "requeue_retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column("requesttask", sa.Column("celery_task_id", sa.String(), nullable=True))
    op.create_index(
        "ix_requesttask_celery_task_id",
        "requesttask",
        ["celery_task_id"],
        unique=False,
    )
    op.add_column(
        "requesttask",
        sa.Column(
            "email_checkpoints",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.create_table(
        "manual_webhook_input",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("privacy_request_id", sa.String(), nullable=False),
        sa.Column("manual_webhook_id", sa.String(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column(
            "input_data",
            encrypted_type(type_in=JSONTypeOverride),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["manual_webhook_id"],
            ["accessmanualwebhook.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"],
            ["privacyrequest.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "privacy_request_id",
            "manual_webhook_id",
            "action_type",
            name="uq_manual_webhook_input_pr_webhook_action",
        ),
    )

    op.create_table(
        "identity_verification_code",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("owner_type", sa.String(), nullable=False),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_type",
            "owner_id",
            name="uq_identity_verification_code_owner",
        ),
    )
    op.create_index(
        "ix_identity_verification_code_expires_at",
        "identity_verification_code",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_identity_verification_code_expires_at",
        table_name="identity_verification_code",
    )
    op.drop_table("identity_verification_code")
    op.drop_table("manual_webhook_input")

    op.drop_column("requesttask", "email_checkpoints")
    op.drop_index("ix_requesttask_celery_task_id", table_name="requesttask")
    op.drop_column("requesttask", "celery_task_id")

    op.drop_column("privacyrequest", "requeue_retry_count")
    op.drop_index("ix_privacyrequest_celery_task_id", table_name="privacyrequest")
    op.drop_column("privacyrequest", "celery_task_id")
    op.drop_column("privacyrequest", "data_use_map")
    op.drop_column("privacyrequest", "failed_action_needed")
    op.drop_column("privacyrequest", "failed_collection")
    op.drop_column("privacyrequest", "failed_step")
    op.drop_column("privacyrequest", "paused_action_needed")
    op.drop_column("privacyrequest", "paused_collection")
    op.drop_column("privacyrequest", "paused_step")
    op.drop_column("privacyrequest", "drp_request_body")
    op.drop_column("privacyrequest", "encryption_key")
