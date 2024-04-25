"""adding custom privacy request field table

Revision ID: ad2e3f9a6850
Revises: 1ea164cee8bc
Create Date: 2023-09-06 20:09:10.188690

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "ad2e3f9a6850"
down_revision = "1ea164cee8bc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "custom_privacy_request_field",
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
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("field_label", sa.String(), nullable=False),
        sa.Column("hashed_value", sa.String(), nullable=True),
        sa.Column(
            "encrypted_value",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"],
            ["privacyrequest.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_custom_privacy_request_field_hashed_value"),
        "custom_privacy_request_field",
        ["hashed_value"],
        unique=False,
    )
    op.create_index(
        op.f("ix_custom_privacy_request_field_id"),
        "custom_privacy_request_field",
        ["id"],
        unique=False,
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "custom_privacy_request_fields_approved_by", sa.String(), nullable=True
        ),
    )
    op.add_column(
        "privacyrequest",
        sa.Column(
            "custom_privacy_request_fields_approved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "privacyrequest_custom_privacy_request_fields_approved_by_fkey",
        "privacyrequest",
        "fidesuser",
        ["custom_privacy_request_fields_approved_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "privacyrequest_custom_privacy_request_fields_approved_by_fkey",
        "privacyrequest",
        type_="foreignkey",
    )
    op.drop_column("privacyrequest", "custom_privacy_request_fields_approved_at")
    op.drop_column("privacyrequest", "custom_privacy_request_fields_approved_by")
    op.drop_index(
        op.f("ix_custom_privacy_request_field_id"),
        table_name="custom_privacy_request_field",
    )
    op.drop_index(
        op.f("ix_custom_privacy_request_field_hashed_value"),
        table_name="custom_privacy_request_field",
    )
    op.drop_table("custom_privacy_request_field")
