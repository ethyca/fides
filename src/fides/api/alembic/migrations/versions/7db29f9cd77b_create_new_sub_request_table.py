"""Create new Sub Request Table

Revision ID: 7db29f9cd77b
Revises: b97e92b038d2
Create Date: 2025-09-16 14:00:16.282996

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import JSONTypeOverride
from fides.config import CONFIG

# revision identifiers, used by Alembic.
revision = "7db29f9cd77b"
down_revision = "b97e92b038d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "request_task_sub_request",
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
        sa.Column("request_task_id", sa.String(length=255), nullable=False),
        sa.Column(
            "param_values",
            StringEncryptedType(
                type_in=JSONTypeOverride,
                key=CONFIG.security.app_encryption_key,
                engine=AesGcmEngine,
                padding="pkcs5",
            ),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "access_data",
            StringEncryptedType(
                type_in=JSONTypeOverride,
                key=CONFIG.security.app_encryption_key,
                engine=AesGcmEngine,
                padding="pkcs5",
            ),
            nullable=True,
        ),
        sa.Column("rows_masked", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["request_task_id"],
            ["requesttask.id"],
            name="request_task_sub_request_request_task_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_request_task_sub_request_id"),
        "request_task_sub_request",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_request_task_sub_request_request_task_id"),
        "request_task_sub_request",
        ["request_task_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_request_task_sub_request_request_task_id"),
        table_name="request_task_sub_request",
    )
    op.drop_index(
        op.f("ix_request_task_sub_request_id"), table_name="request_task_sub_request"
    )
    op.drop_table("request_task_sub_request")
