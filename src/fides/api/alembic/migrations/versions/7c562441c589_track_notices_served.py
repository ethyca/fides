"""track notices served

Revision ID: 7c562441c589
Revises: 7315b9d7fda6
Create Date: 2023-07-10 16:42:37.433995

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "7c562441c589"
down_revision = "7315b9d7fda6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "servednoticehistory",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "anonymized_ip_address",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "email",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "fides_user_device",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("request_origin", sa.String(), nullable=True),
        sa.Column("url_recorded", sa.String(), nullable=True),
        sa.Column(
            "user_agent",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("user_geography", sa.String(), nullable=True),
        sa.Column("acknowledge_mode", sa.Boolean(), nullable=True),
        sa.Column("serving_component", sa.String(), nullable=False),
        sa.Column("fides_user_device_provided_identity_id", sa.String(), nullable=True),
        sa.Column("privacy_experience_config_history_id", sa.String(), nullable=True),
        sa.Column("privacy_experience_id", sa.String(), nullable=True),
        sa.Column("privacy_notice_history_id", sa.String(), nullable=False),
        sa.Column("provided_identity_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["fides_user_device_provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_experience_config_history_id"],
            ["privacyexperienceconfighistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_experience_id"],
            ["privacyexperience.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_notice_history_id"],
            ["privacynoticehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_servednoticehistory_created_at"),
        "servednoticehistory",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_fides_user_device_provided_identity_id"),
        "servednoticehistory",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_hashed_email"),
        "servednoticehistory",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_hashed_fides_user_device"),
        "servednoticehistory",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_hashed_phone_number"),
        "servednoticehistory",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_id"), "servednoticehistory", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_servednoticehistory_privacy_experience_config_history_id"),
        "servednoticehistory",
        ["privacy_experience_config_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_privacy_experience_id"),
        "servednoticehistory",
        ["privacy_experience_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_privacy_notice_history_id"),
        "servednoticehistory",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_provided_identity_id"),
        "servednoticehistory",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_serving_component"),
        "servednoticehistory",
        ["serving_component"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_user_geography"),
        "servednoticehistory",
        ["user_geography"],
        unique=False,
    )
    op.create_table(
        "lastservednotice",
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
        sa.Column("served_notice_history_id", sa.String(), nullable=False),
        sa.Column("provided_identity_id", sa.String(), nullable=True),
        sa.Column("fides_user_device_provided_identity_id", sa.String(), nullable=True),
        sa.Column("privacy_notice_id", sa.String(), nullable=False),
        sa.Column("privacy_notice_history_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["fides_user_device_provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_notice_history_id"],
            ["privacynoticehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_notice_id"],
            ["privacynotice.id"],
        ),
        sa.ForeignKeyConstraint(
            ["provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.ForeignKeyConstraint(
            ["served_notice_history_id"],
            ["servednoticehistory.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "privacy_notice_id",
            name="last_served_fides_user_device_identity_privacy_notice",
        ),
        sa.UniqueConstraint(
            "provided_identity_id",
            "privacy_notice_id",
            name="last_served_identity_privacy_notice",
        ),
    )
    op.create_index(
        op.f("ix_lastservednotice_created_at"),
        "lastservednotice",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_fides_user_device_provided_identity_id"),
        "lastservednotice",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_id"), "lastservednotice", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_lastservednotice_privacy_notice_history_id"),
        "lastservednotice",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_privacy_notice_id"),
        "lastservednotice",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_provided_identity_id"),
        "lastservednotice",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_served_notice_history_id"),
        "lastservednotice",
        ["served_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_updated_at"),
        "lastservednotice",
        ["updated_at"],
        unique=False,
    )

    op.add_column(
        "privacypreferencehistory",
        sa.Column("served_notice_history_id", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_served_notice_history_id"),
        "privacypreferencehistory",
        ["served_notice_history_id"],
        unique=False,
    )
    op.create_foreign_key(
        "privacy_preference_served_notice_fk",
        "privacypreferencehistory",
        "servednoticehistory",
        ["served_notice_history_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "privacy_preference_served_notice_fk",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_served_notice_history_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "served_notice_history_id")
    op.drop_index(op.f("ix_lastservednotice_updated_at"), table_name="lastservednotice")
    op.drop_index(
        op.f("ix_lastservednotice_served_notice_history_id"),
        table_name="lastservednotice",
    )
    op.drop_index(
        op.f("ix_lastservednotice_provided_identity_id"), table_name="lastservednotice"
    )
    op.drop_index(
        op.f("ix_lastservednotice_privacy_notice_id"), table_name="lastservednotice"
    )
    op.drop_index(
        op.f("ix_lastservednotice_privacy_notice_history_id"),
        table_name="lastservednotice",
    )
    op.drop_index(op.f("ix_lastservednotice_id"), table_name="lastservednotice")
    op.drop_index(
        op.f("ix_lastservednotice_fides_user_device_provided_identity_id"),
        table_name="lastservednotice",
    )
    op.drop_index(op.f("ix_lastservednotice_created_at"), table_name="lastservednotice")
    op.drop_table("lastservednotice")
    op.drop_index(
        op.f("ix_servednoticehistory_user_geography"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_serving_component"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_provided_identity_id"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_privacy_notice_history_id"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_privacy_experience_id"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_privacy_experience_config_history_id"),
        table_name="servednoticehistory",
    )
    op.drop_index(op.f("ix_servednoticehistory_id"), table_name="servednoticehistory")
    op.drop_index(
        op.f("ix_servednoticehistory_hashed_phone_number"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_hashed_fides_user_device"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_hashed_email"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_fides_user_device_provided_identity_id"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_created_at"), table_name="servednoticehistory"
    )
    op.drop_table("servednoticehistory")
