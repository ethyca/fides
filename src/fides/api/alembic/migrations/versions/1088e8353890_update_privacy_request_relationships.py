"""update privacy request relationships

Revision ID: 1088e8353890
Revises: d9237a0c0d5a
Create Date: 2024-12-26 22:38:37.905571

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1088e8353890"
down_revision = "d9237a0c0d5a"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "custom_privacy_request_field_privacy_request_id_fkey",
        "custom_privacy_request_field",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "custom_privacy_request_field_privacy_request_id_fkey",
        "custom_privacy_request_field",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "providedidentity_privacy_request_id_fkey",
        "providedidentity",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "providedidentity_privacy_request_id_fkey",
        "providedidentity",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "privacyrequesterror_privacy_request_id_fkey",
        "privacyrequesterror",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "privacyrequesterror_privacy_request_id_fkey",
        "privacyrequesterror",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        "providedidentity_privacy_request_id_fkey",
        "providedidentity",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "providedidentity_privacy_request_id_fkey",
        "providedidentity",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
    )
    op.drop_constraint(
        "custom_privacy_request_field_privacy_request_id_fkey",
        "custom_privacy_request_field",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "custom_privacy_request_field_privacy_request_id_fkey",
        "custom_privacy_request_field",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
    )
    op.drop_constraint(
        "privacyrequesterror_privacy_request_id_fkey",
        "privacyrequesterror",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "privacyrequesterror_privacy_request_id_fkey",
        "privacyrequesterror",
        "privacyrequest",
        ["privacy_request_id"],
        ["id"],
    )
