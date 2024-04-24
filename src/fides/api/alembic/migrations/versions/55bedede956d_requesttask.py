"""requesttask

Revision ID: 55bedede956d
Revises: 6cfd59e7920a
Create Date: 2024-04-04 04:12:25.332952

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "55bedede956d"
down_revision = "6cfd59e7920a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "requesttask",
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
        sa.Column("privacy_request_id", sa.String(), nullable=True),
        sa.Column("collection_address", sa.String(), nullable=False),
        sa.Column("dataset_name", sa.String(), nullable=False),
        sa.Column("collection_name", sa.String(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "upstream_tasks", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "downstream_tasks", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "all_descendant_tasks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "access_data",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "data_for_erasures",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("rows_masked", sa.Integer(), nullable=True),
        sa.Column("consent_sent", sa.Boolean(), nullable=True),
        sa.Column("collection", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "traversal_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"], ["privacyrequest.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_requesttask_action_type"), "requesttask", ["action_type"], unique=False
    )
    op.create_index(
        op.f("ix_requesttask_collection_address"),
        "requesttask",
        ["collection_address"],
        unique=False,
    )
    op.create_index(
        op.f("ix_requesttask_collection_name"),
        "requesttask",
        ["collection_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_requesttask_dataset_name"),
        "requesttask",
        ["dataset_name"],
        unique=False,
    )
    op.create_index(op.f("ix_requesttask_id"), "requesttask", ["id"], unique=False)
    op.create_index(
        op.f("ix_requesttask_privacy_request_id"),
        "requesttask",
        ["privacy_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_requesttask_status"), "requesttask", ["status"], unique=False
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "filtered_final_upload",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "access_result_urls",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("privacyrequest", "access_result_urls")
    op.drop_column("privacyrequest", "filtered_final_upload")
    op.drop_index(op.f("ix_requesttask_status"), table_name="requesttask")
    op.drop_index(op.f("ix_requesttask_privacy_request_id"), table_name="requesttask")
    op.drop_index(op.f("ix_requesttask_id"), table_name="requesttask")
    op.drop_index(op.f("ix_requesttask_dataset_name"), table_name="requesttask")
    op.drop_index(op.f("ix_requesttask_collection_name"), table_name="requesttask")
    op.drop_index(op.f("ix_requesttask_collection_address"), table_name="requesttask")
    op.drop_index(op.f("ix_requesttask_action_type"), table_name="requesttask")
    op.drop_table("requesttask")
