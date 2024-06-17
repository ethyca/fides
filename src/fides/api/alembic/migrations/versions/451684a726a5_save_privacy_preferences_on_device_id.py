"""save privacy preferences on device id

Revision ID: 451684a726a5
Revises: 48d9caacebd4
Create Date: 2023-04-23 16:06:19.788074

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "451684a726a5"
down_revision = "48d9caacebd4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "currentprivacypreference",
        sa.Column("fides_user_device_provided_identity_id", sa.String(), nullable=True),
    )
    op.create_unique_constraint(
        "fides_user_device_identity_privacy_notice",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "privacy_notice_id"],
    )
    op.create_index(
        op.f("ix_currentprivacypreference_fides_user_device_provided_identity_id"),
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_foreign_key(
        "currentprivacypreference_fides_user_device_provided_identi_fkey",
        "currentprivacypreference",
        "providedidentity",
        ["fides_user_device_provided_identity_id"],
        ["id"],
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "fides_user_device",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("fides_user_device_provided_identity_id", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_fides_user_device_provided_identity_id"),
        "privacypreferencehistory",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_hashed_fides_user_device"),
        "privacypreferencehistory",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_foreign_key(
        "privacypreferencehistory_fides_user_device_provided_identi_fkey",
        "privacypreferencehistory",
        "providedidentity",
        ["fides_user_device_provided_identity_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "privacypreferencehistory_fides_user_device_provided_identi_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_hashed_fides_user_device"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_fides_user_device_provided_identity_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "hashed_fides_user_device")
    op.drop_column("privacypreferencehistory", "fides_user_device_provided_identity_id")
    op.drop_column("privacypreferencehistory", "fides_user_device")
    op.drop_constraint(
        "currentprivacypreference_fides_user_device_provided_identi_fkey",
        "currentprivacypreference",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_fides_user_device_provided_identity_id"),
        table_name="currentprivacypreference",
    )
    op.drop_constraint(
        "fides_user_device_identity_privacy_notice",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_column("currentprivacypreference", "fides_user_device_provided_identity_id")
