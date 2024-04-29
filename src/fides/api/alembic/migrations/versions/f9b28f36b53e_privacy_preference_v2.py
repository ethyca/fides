"""privacy_preference_v2

Revision ID: f9b28f36b53e
Revises: f396c1f84b0f
Create Date: 2023-12-13 17:14:00.677493

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

from fides.api.models.privacy_notice import ConsentMechanism

revision = "f9b28f36b53e"
down_revision = "f396c1f84b0f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "currentprivacypreferencev2",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("fides_string", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="last_saved_for_email"),
        sa.UniqueConstraint(
            "fides_user_device", name="last_saved_for_fides_user_device"
        ),
        sa.UniqueConstraint("phone_number", name="last_saved_for_phone_number"),
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_created_at"),
        "currentprivacypreferencev2",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_hashed_email"),
        "currentprivacypreferencev2",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_hashed_fides_user_device"),
        "currentprivacypreferencev2",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_hashed_phone_number"),
        "currentprivacypreferencev2",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_id"),
        "currentprivacypreferencev2",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_updated_at"),
        "currentprivacypreferencev2",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        "lastservednoticev2",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("served", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="last_served_for_email"),
        sa.UniqueConstraint(
            "fides_user_device", name="last_served_for_fides_user_device"
        ),
        sa.UniqueConstraint("phone_number", name="last_served_for_phone_number"),
    )
    op.create_index(
        op.f("ix_lastservednoticev2_created_at"),
        "lastservednoticev2",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_hashed_email"),
        "lastservednoticev2",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_hashed_fides_user_device"),
        "lastservednoticev2",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_hashed_phone_number"),
        "lastservednoticev2",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_id"), "lastservednoticev2", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_lastservednoticev2_updated_at"),
        "lastservednoticev2",
        ["updated_at"],
        unique=False,
    )
    op.drop_index(
        "ix_currentprivacypreference_privacy_preference_history_id",
        table_name="currentprivacypreference",
    )
    op.drop_constraint(
        "currentprivacypreference_privacy_preference_history_id_fkey",
        "currentprivacypreference",
        type_="foreignkey",
    )
    # Getting rid of this link - currentprivacypreference is deprecated and we need to drop this existing connection
    op.drop_column("currentprivacypreference", "privacy_preference_history_id")
    op.drop_index(
        "ix_lastservednotice_served_notice_history_id", table_name="lastservednotice"
    )
    op.drop_constraint(
        "lastservednotice_served_notice_history_id_fkey",
        "lastservednotice",
        type_="foreignkey",
    )
    # Getting rid of this link - lastservednotice is deprecated and we need to drop this existing connection
    op.drop_column("lastservednotice", "served_notice_history_id")
    op.add_column(
        "privacypreferencehistory", sa.Column("notice_key", sa.String(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("notice_mechanism", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("notice_name", sa.String(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("fides_string", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "tcf_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.alter_column(
        "privacypreferencehistory",
        "preference",
        type_=sa.String(),
        existing_type=sa.Enum(ConsentMechanism),
    )
    op.drop_index(
        "ix_privacypreferencehistory_feature", table_name="privacypreferencehistory"
    )
    op.drop_index(
        "ix_privacypreferencehistory_fides_user_device_provided__9961",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_provided_identity_id",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_purpose_consent",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_purpose_legitimate_interests",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_special_feature",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_special_purpose",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_system_consent",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_system_legitimate_interests",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_vendor_consent",
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        "ix_privacypreferencehistory_vendor_legitimate_interests",
        table_name="privacypreferencehistory",
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_notice_key"),
        "privacypreferencehistory",
        ["notice_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_notice_mechanism"),
        "privacypreferencehistory",
        ["notice_mechanism"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_notice_name"),
        "privacypreferencehistory",
        ["notice_name"],
        unique=False,
    )
    op.drop_constraint(
        "privacypreferencehistory_provided_identity_id_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_constraint(
        "privacypreferencehistory_fides_user_device_provided_identi_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_constraint(
        "privacy_preference_served_notice_fk",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_column("privacypreferencehistory", "vendor_consent")
    op.drop_column("privacypreferencehistory", "purpose_consent")
    op.drop_column("privacypreferencehistory", "purpose_legitimate_interests")
    op.drop_column("privacypreferencehistory", "system_legitimate_interests")
    op.drop_column("privacypreferencehistory", "fides_user_device_provided_identity_id")
    op.drop_column("privacypreferencehistory", "special_feature")
    op.drop_column("privacypreferencehistory", "special_purpose")
    op.drop_column("privacypreferencehistory", "tcf_version")
    op.drop_column("privacypreferencehistory", "system_consent")
    op.drop_column("privacypreferencehistory", "relevant_systems")
    op.drop_column("privacypreferencehistory", "vendor_legitimate_interests")
    op.drop_column("privacypreferencehistory", "feature")
    op.drop_column("privacypreferencehistory", "provided_identity_id")
    op.add_column(
        "servednoticehistory", sa.Column("notice_key", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("notice_mechanism", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("notice_name", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("served_notice_history_id", sa.String(), nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("tcf_served", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.drop_index("ix_servednoticehistory_feature", table_name="servednoticehistory")
    op.drop_index(
        "ix_servednoticehistory_fides_user_device_provided_identity_id",
        table_name="servednoticehistory",
    )
    op.drop_index(
        "ix_servednoticehistory_provided_identity_id", table_name="servednoticehistory"
    )
    op.drop_index(
        "ix_servednoticehistory_purpose_consent", table_name="servednoticehistory"
    )
    op.drop_index(
        "ix_servednoticehistory_purpose_legitimate_interests",
        table_name="servednoticehistory",
    )
    op.drop_index(
        "ix_servednoticehistory_special_feature", table_name="servednoticehistory"
    )
    op.drop_index(
        "ix_servednoticehistory_special_purpose", table_name="servednoticehistory"
    )
    op.drop_index(
        "ix_servednoticehistory_system_consent", table_name="servednoticehistory"
    )
    op.drop_index(
        "ix_servednoticehistory_system_legitimate_interests",
        table_name="servednoticehistory",
    )
    op.drop_index(
        "ix_servednoticehistory_vendor_consent", table_name="servednoticehistory"
    )
    op.drop_index(
        "ix_servednoticehistory_vendor_legitimate_interests",
        table_name="servednoticehistory",
    )
    op.create_index(
        op.f("ix_servednoticehistory_notice_key"),
        "servednoticehistory",
        ["notice_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_notice_mechanism"),
        "servednoticehistory",
        ["notice_mechanism"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_notice_name"),
        "servednoticehistory",
        ["notice_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_served_notice_history_id"),
        "servednoticehistory",
        ["served_notice_history_id"],
        unique=False,
    )
    op.drop_constraint(
        "servednoticehistory_provided_identity_id_fkey",
        "servednoticehistory",
        type_="foreignkey",
    )
    op.drop_constraint(
        "servednoticehistory_fides_user_device_provided_identity_id_fkey",
        "servednoticehistory",
        type_="foreignkey",
    )
    op.drop_column("servednoticehistory", "vendor_consent")
    op.drop_column("servednoticehistory", "purpose_consent")
    op.drop_column("servednoticehistory", "purpose_legitimate_interests")
    op.drop_column("servednoticehistory", "system_legitimate_interests")
    op.drop_column("servednoticehistory", "fides_user_device_provided_identity_id")
    op.drop_column("servednoticehistory", "special_feature")
    op.drop_column("servednoticehistory", "special_purpose")
    op.drop_column("servednoticehistory", "tcf_version")
    op.drop_column("servednoticehistory", "system_consent")
    op.drop_column("servednoticehistory", "vendor_legitimate_interests")
    op.drop_column("servednoticehistory", "feature")
    op.drop_column("servednoticehistory", "provided_identity_id")


def downgrade():
    op.alter_column(
        "privacypreferencehistory",
        "preference",
        type_=sa.Enum(ConsentMechanism),
        existing_type=sa.String(),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column(
            "provided_identity_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("feature", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column(
            "vendor_legitimate_interests",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("system_consent", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("tcf_version", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("special_purpose", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("special_feature", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column(
            "fides_user_device_provided_identity_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column(
            "system_legitimate_interests",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column(
            "purpose_legitimate_interests",
            sa.INTEGER(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("purpose_consent", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("vendor_consent", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "servednoticehistory_fides_user_device_provided_identity_id_fkey",
        "servednoticehistory",
        "providedidentity",
        ["fides_user_device_provided_identity_id"],
        ["id"],
    )
    op.create_foreign_key(
        "servednoticehistory_provided_identity_id_fkey",
        "servednoticehistory",
        "providedidentity",
        ["provided_identity_id"],
        ["id"],
    )
    op.drop_index(
        op.f("ix_servednoticehistory_served_notice_history_id"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_notice_name"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_notice_mechanism"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_notice_key"), table_name="servednoticehistory"
    )
    op.create_index(
        "ix_servednoticehistory_vendor_legitimate_interests",
        "servednoticehistory",
        ["vendor_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_vendor_consent",
        "servednoticehistory",
        ["vendor_consent"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_system_legitimate_interests",
        "servednoticehistory",
        ["system_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_system_consent",
        "servednoticehistory",
        ["system_consent"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_special_purpose",
        "servednoticehistory",
        ["special_purpose"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_special_feature",
        "servednoticehistory",
        ["special_feature"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_purpose_legitimate_interests",
        "servednoticehistory",
        ["purpose_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_purpose_consent",
        "servednoticehistory",
        ["purpose_consent"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_provided_identity_id",
        "servednoticehistory",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_fides_user_device_provided_identity_id",
        "servednoticehistory",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        "ix_servednoticehistory_feature",
        "servednoticehistory",
        ["feature"],
        unique=False,
    )
    op.drop_column("servednoticehistory", "tcf_served")
    op.drop_column("servednoticehistory", "served_notice_history_id")
    op.drop_column("servednoticehistory", "notice_name")
    op.drop_column("servednoticehistory", "notice_mechanism")
    op.drop_column("servednoticehistory", "notice_key")
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "provided_identity_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("feature", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "vendor_legitimate_interests",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "relevant_systems",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("system_consent", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("tcf_version", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("special_purpose", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("special_feature", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "fides_user_device_provided_identity_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "system_legitimate_interests",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "purpose_legitimate_interests",
            sa.INTEGER(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("purpose_consent", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("vendor_consent", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "privacy_preference_served_notice_fk",
        "privacypreferencehistory",
        "servednoticehistory",
        ["served_notice_history_id"],
        ["id"],
    )
    op.create_foreign_key(
        "privacypreferencehistory_fides_user_device_provided_identi_fkey",
        "privacypreferencehistory",
        "providedidentity",
        ["fides_user_device_provided_identity_id"],
        ["id"],
    )
    op.create_foreign_key(
        "privacypreferencehistory_provided_identity_id_fkey",
        "privacypreferencehistory",
        "providedidentity",
        ["provided_identity_id"],
        ["id"],
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_notice_name"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_notice_mechanism"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_notice_key"),
        table_name="privacypreferencehistory",
    )
    op.create_index(
        "ix_privacypreferencehistory_vendor_legitimate_interests",
        "privacypreferencehistory",
        ["vendor_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_vendor_consent",
        "privacypreferencehistory",
        ["vendor_consent"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_system_legitimate_interests",
        "privacypreferencehistory",
        ["system_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_system_consent",
        "privacypreferencehistory",
        ["system_consent"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_special_purpose",
        "privacypreferencehistory",
        ["special_purpose"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_special_feature",
        "privacypreferencehistory",
        ["special_feature"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_purpose_legitimate_interests",
        "privacypreferencehistory",
        ["purpose_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_purpose_consent",
        "privacypreferencehistory",
        ["purpose_consent"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_provided_identity_id",
        "privacypreferencehistory",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_fides_user_device_provided__9961",
        "privacypreferencehistory",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_feature",
        "privacypreferencehistory",
        ["feature"],
        unique=False,
    )
    op.drop_column("privacypreferencehistory", "tcf_preferences")
    op.drop_column("privacypreferencehistory", "fides_string")
    op.drop_column("privacypreferencehistory", "notice_name")
    op.drop_column("privacypreferencehistory", "notice_mechanism")
    op.drop_column("privacypreferencehistory", "notice_key")
    op.add_column(
        "lastservednotice",
        sa.Column(
            "served_notice_history_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.create_index(
        "ix_lastservednotice_served_notice_history_id",
        "lastservednotice",
        ["served_notice_history_id"],
        unique=False,
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column(
            "privacy_preference_history_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_index(
        "ix_currentprivacypreference_privacy_preference_history_id",
        "currentprivacypreference",
        ["privacy_preference_history_id"],
        unique=False,
    )
    op.create_index("ix_ctl_systems_name", "ctl_systems", ["name"], unique=False)
    op.drop_index(
        op.f("ix_lastservednoticev2_updated_at"), table_name="lastservednoticev2"
    )
    op.drop_index(op.f("ix_lastservednoticev2_id"), table_name="lastservednoticev2")
    op.drop_index(
        op.f("ix_lastservednoticev2_hashed_phone_number"),
        table_name="lastservednoticev2",
    )
    op.drop_index(
        op.f("ix_lastservednoticev2_hashed_fides_user_device"),
        table_name="lastservednoticev2",
    )
    op.drop_index(
        op.f("ix_lastservednoticev2_hashed_email"), table_name="lastservednoticev2"
    )
    op.drop_index(
        op.f("ix_lastservednoticev2_created_at"), table_name="lastservednoticev2"
    )
    op.drop_table("lastservednoticev2")
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_updated_at"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_id"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_phone_number"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_fides_user_device"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_email"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_created_at"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_table("currentprivacypreferencev2")
