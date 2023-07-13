"""tcf_tables

Revision ID: 3d4576bb0320
Revises: 7c562441c589
Create Date: 2023-07-13 19:02:58.975871

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3d4576bb0320"
down_revision = "7c562441c589"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tcfdatause",
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
        sa.Column(
            "consent_mechanism",
            sa.String(),
            nullable=True,
        ),
        sa.Column(
            "enforcement_level",
            sa.String(),
            nullable=True,
        ),
        sa.Column("has_gpc_flag", sa.Boolean(), nullable=True),
        sa.Column("notice_key", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tcfdatause_id"), "tcfdatause", ["id"], unique=False)
    op.create_table(
        "lastserveddatause",
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
        sa.Column("data_use", sa.String(), nullable=False),
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
            "data_use",
            name="last_served_fides_user_device_identity_data_use",
        ),
        sa.UniqueConstraint(
            "provided_identity_id", "data_use", name="last_served_identity_data_use"
        ),
    )
    op.create_index(
        op.f("ix_lastserveddatause_created_at"),
        "lastserveddatause",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastserveddatause_data_use"),
        "lastserveddatause",
        ["data_use"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastserveddatause_fides_user_device_provided_identity_id"),
        "lastserveddatause",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastserveddatause_id"), "lastserveddatause", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_lastserveddatause_privacy_notice_history_id"),
        "lastserveddatause",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastserveddatause_privacy_notice_id"),
        "lastserveddatause",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastserveddatause_provided_identity_id"),
        "lastserveddatause",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastserveddatause_served_notice_history_id"),
        "lastserveddatause",
        ["served_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastserveddatause_updated_at"),
        "lastserveddatause",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        "lastservedfeature",
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
        sa.Column("feature", sa.String(), nullable=False),
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
            "feature",
            name="last_served_fides_user_device_identity_feature",
        ),
        sa.UniqueConstraint(
            "provided_identity_id", "feature", name="last_served_identity_feature"
        ),
    )
    op.create_index(
        op.f("ix_lastservedfeature_created_at"),
        "lastservedfeature",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedfeature_feature"),
        "lastservedfeature",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedfeature_fides_user_device_provided_identity_id"),
        "lastservedfeature",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedfeature_id"), "lastservedfeature", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_lastservedfeature_privacy_notice_history_id"),
        "lastservedfeature",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedfeature_privacy_notice_id"),
        "lastservedfeature",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedfeature_provided_identity_id"),
        "lastservedfeature",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedfeature_served_notice_history_id"),
        "lastservedfeature",
        ["served_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedfeature_updated_at"),
        "lastservedfeature",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        "lastservedvendor",
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
        sa.Column("vendor", sa.String(), nullable=False),
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
            "vendor",
            name="last_served_fides_user_device_identity_vendor",
        ),
        sa.UniqueConstraint(
            "provided_identity_id", "vendor", name="last_served_identity_vendor"
        ),
    )
    op.create_index(
        op.f("ix_lastservedvendor_created_at"),
        "lastservedvendor",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedvendor_fides_user_device_provided_identity_id"),
        "lastservedvendor",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedvendor_id"), "lastservedvendor", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_lastservedvendor_privacy_notice_history_id"),
        "lastservedvendor",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedvendor_privacy_notice_id"),
        "lastservedvendor",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedvendor_provided_identity_id"),
        "lastservedvendor",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedvendor_served_notice_history_id"),
        "lastservedvendor",
        ["served_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedvendor_updated_at"),
        "lastservedvendor",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservedvendor_vendor"), "lastservedvendor", ["vendor"], unique=False
    )
    op.create_table(
        "currentdatausepreference",
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
        sa.Column(
            "preference",
            sa.String(),
            nullable=False,
        ),
        sa.Column("data_use", sa.String(), nullable=False),
        sa.Column("privacy_preference_history_id", sa.String(), nullable=False),
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
            ["privacy_preference_history_id"],
            ["privacypreferencehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "data_use",
            name="fides_user_device_identity_data_use",
        ),
        sa.UniqueConstraint(
            "provided_identity_id", "data_use", name="identity_data_use"
        ),
    )
    op.create_index(
        op.f("ix_currentdatausepreference_created_at"),
        "currentdatausepreference",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_data_use"),
        "currentdatausepreference",
        ["data_use"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_fides_user_device_provided_identity_id"),
        "currentdatausepreference",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_id"),
        "currentdatausepreference",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_preference"),
        "currentdatausepreference",
        ["preference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_privacy_notice_history_id"),
        "currentdatausepreference",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_privacy_notice_id"),
        "currentdatausepreference",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_privacy_preference_history_id"),
        "currentdatausepreference",
        ["privacy_preference_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_provided_identity_id"),
        "currentdatausepreference",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentdatausepreference_updated_at"),
        "currentdatausepreference",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        "currentfeaturepreference",
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
        sa.Column(
            "preference",
            sa.String(),
            nullable=False,
        ),
        sa.Column("feature", sa.String(), nullable=False),
        sa.Column("privacy_preference_history_id", sa.String(), nullable=False),
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
            ["privacy_preference_history_id"],
            ["privacypreferencehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "feature",
            name="fides_user_device_identity_feature",
        ),
        sa.UniqueConstraint("provided_identity_id", "feature", name="identity_feature"),
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_created_at"),
        "currentfeaturepreference",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_feature"),
        "currentfeaturepreference",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_fides_user_device_provided_identity_id"),
        "currentfeaturepreference",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_id"),
        "currentfeaturepreference",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_preference"),
        "currentfeaturepreference",
        ["preference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_privacy_notice_history_id"),
        "currentfeaturepreference",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_privacy_notice_id"),
        "currentfeaturepreference",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_privacy_preference_history_id"),
        "currentfeaturepreference",
        ["privacy_preference_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_provided_identity_id"),
        "currentfeaturepreference",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentfeaturepreference_updated_at"),
        "currentfeaturepreference",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        "currentvendorpreference",
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
        sa.Column(
            "preference",
            sa.String(),
            nullable=False,
        ),
        sa.Column("vendor", sa.String(), nullable=False),
        sa.Column("privacy_preference_history_id", sa.String(), nullable=False),
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
            ["privacy_preference_history_id"],
            ["privacypreferencehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fides_user_device_provided_identity_id",
            "vendor",
            name="fides_user_device_identity_vendor",
        ),
        sa.UniqueConstraint("provided_identity_id", "vendor", name="identity_vendor"),
    )
    op.create_index(
        op.f("ix_currentvendorpreference_created_at"),
        "currentvendorpreference",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_fides_user_device_provided_identity_id"),
        "currentvendorpreference",
        ["fides_user_device_provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_id"),
        "currentvendorpreference",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_preference"),
        "currentvendorpreference",
        ["preference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_privacy_notice_history_id"),
        "currentvendorpreference",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_privacy_notice_id"),
        "currentvendorpreference",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_privacy_preference_history_id"),
        "currentvendorpreference",
        ["privacy_preference_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_provided_identity_id"),
        "currentvendorpreference",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_updated_at"),
        "currentvendorpreference",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentvendorpreference_vendor"),
        "currentvendorpreference",
        ["vendor"],
        unique=False,
    )
    op.add_column(
        "privacynotice",
        sa.Column("displayed_in_tcf_overlay", sa.Boolean(), nullable=True),
    )
    op.add_column("privacynotice", sa.Column("is_tcf", sa.Boolean(), nullable=True))
    op.alter_column(
        "privacynotice",
        "consent_mechanism",
        existing_type=sa.String(),
        nullable=True,
    )
    op.alter_column(
        "privacynotice", "enforcement_level", existing_type=sa.VARCHAR(), nullable=True
    )
    op.alter_column(
        "privacynotice", "has_gpc_flag", existing_type=sa.BOOLEAN(), nullable=True
    )
    op.alter_column(
        "privacynotice", "notice_key", existing_type=sa.VARCHAR(), nullable=True
    )
    op.add_column(
        "privacynoticehistory",
        sa.Column("displayed_in_tcf_overlay", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "privacynoticehistory", sa.Column("is_tcf", sa.Boolean(), nullable=True)
    )
    op.alter_column(
        "privacynoticehistory",
        "consent_mechanism",
        existing_type=sa.String(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory",
        "enforcement_level",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory",
        "has_gpc_flag",
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory", "notice_key", existing_type=sa.VARCHAR(), nullable=True
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column("displayed_in_tcf_overlay", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "privacynoticetemplate", sa.Column("is_tcf", sa.Boolean(), nullable=True)
    )
    op.alter_column(
        "privacynoticetemplate",
        "consent_mechanism",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticetemplate",
        "enforcement_level",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticetemplate",
        "has_gpc_flag",
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticetemplate", "notice_key", existing_type=sa.VARCHAR(), nullable=True
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("data_use", sa.String(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("vendor", sa.String(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("feature", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_data_use"),
        "privacypreferencehistory",
        ["data_use"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_feature"),
        "privacypreferencehistory",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_vendor"),
        "privacypreferencehistory",
        ["vendor"],
        unique=False,
    )
    op.add_column(
        "servednoticehistory", sa.Column("data_use", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("vendor", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("feature", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_servednoticehistory_data_use"),
        "servednoticehistory",
        ["data_use"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_feature"),
        "servednoticehistory",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_vendor"),
        "servednoticehistory",
        ["vendor"],
        unique=False,
    )

    bind = op.get_bind()
    bind.execute(
        f"UPDATE privacynoticetemplate SET displayed_in_tcf_overlay = false;"
    )

    # update our column to make it non-nullable now that it's populated
    op.alter_column("privacynoticetemplate", "displayed_in_tcf_overlay", nullable=False)

    bind.execute(
        f"UPDATE privacynotice SET displayed_in_tcf_overlay = false;"
    )

    # update our column to make it non-nullable now that it's populated
    op.alter_column("privacynotice", "displayed_in_tcf_overlay", nullable=False)

    bind.execute(
        f"UPDATE privacynoticehistory SET displayed_in_tcf_overlay = false;"
    )

    # update our column to make it non-nullable now that it's populated
    op.alter_column("privacynoticehistory", "displayed_in_tcf_overlay", nullable=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_servednoticehistory_vendor"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_feature"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_data_use"), table_name="servednoticehistory"
    )
    op.drop_column("servednoticehistory", "feature")
    op.drop_column("servednoticehistory", "vendor")
    op.drop_column("servednoticehistory", "data_use")
    op.drop_index(
        op.f("ix_privacypreferencehistory_vendor"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_feature"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_data_use"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "feature")
    op.drop_column("privacypreferencehistory", "vendor")
    op.drop_column("privacypreferencehistory", "data_use")
    op.alter_column(
        "privacynoticetemplate",
        "notice_key",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.alter_column(
        "privacynoticetemplate",
        "has_gpc_flag",
        existing_type=sa.BOOLEAN(),
        nullable=False,
    )
    op.alter_column(
        "privacynoticetemplate",
        "enforcement_level",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.alter_column(
        "privacynoticetemplate",
        "consent_mechanism",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.drop_column("privacynoticetemplate", "is_tcf")
    op.drop_column("privacynoticetemplate", "displayed_in_tcf_overlay")
    op.alter_column(
        "privacynoticehistory", "notice_key", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column(
        "privacynoticehistory",
        "has_gpc_flag",
        existing_type=sa.BOOLEAN(),
        nullable=False,
    )
    op.alter_column(
        "privacynoticehistory",
        "enforcement_level",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.alter_column(
        "privacynoticehistory",
        "consent_mechanism",
        existing_type=postgresql.ENUM(
            "opt_in", "opt_out", "notice_only", name="consentmechanism"
        ),
        nullable=False,
    )
    op.drop_column("privacynoticehistory", "is_tcf")
    op.drop_column("privacynoticehistory", "displayed_in_tcf_overlay")
    op.alter_column(
        "privacynotice", "notice_key", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column(
        "privacynotice", "has_gpc_flag", existing_type=sa.BOOLEAN(), nullable=False
    )
    op.alter_column(
        "privacynotice", "enforcement_level", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column(
        "privacynotice",
        "consent_mechanism",
        existing_type=sa.String(),
        nullable=False,
    )
    op.drop_column("privacynotice", "is_tcf")
    op.drop_column("privacynotice", "displayed_in_tcf_overlay")
    op.drop_index(
        op.f("ix_currentvendorpreference_vendor"), table_name="currentvendorpreference"
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_updated_at"),
        table_name="currentvendorpreference",
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_provided_identity_id"),
        table_name="currentvendorpreference",
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_privacy_preference_history_id"),
        table_name="currentvendorpreference",
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_privacy_notice_id"),
        table_name="currentvendorpreference",
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_privacy_notice_history_id"),
        table_name="currentvendorpreference",
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_preference"),
        table_name="currentvendorpreference",
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_id"), table_name="currentvendorpreference"
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_fides_user_device_provided_identity_id"),
        table_name="currentvendorpreference",
    )
    op.drop_index(
        op.f("ix_currentvendorpreference_created_at"),
        table_name="currentvendorpreference",
    )
    op.drop_table("currentvendorpreference")
    op.drop_index(
        op.f("ix_currentfeaturepreference_updated_at"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_provided_identity_id"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_privacy_preference_history_id"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_privacy_notice_id"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_privacy_notice_history_id"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_preference"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_id"), table_name="currentfeaturepreference"
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_fides_user_device_provided_identity_id"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_feature"),
        table_name="currentfeaturepreference",
    )
    op.drop_index(
        op.f("ix_currentfeaturepreference_created_at"),
        table_name="currentfeaturepreference",
    )
    op.drop_table("currentfeaturepreference")
    op.drop_index(
        op.f("ix_currentdatausepreference_updated_at"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_provided_identity_id"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_privacy_preference_history_id"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_privacy_notice_id"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_privacy_notice_history_id"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_preference"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_id"), table_name="currentdatausepreference"
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_fides_user_device_provided_identity_id"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_data_use"),
        table_name="currentdatausepreference",
    )
    op.drop_index(
        op.f("ix_currentdatausepreference_created_at"),
        table_name="currentdatausepreference",
    )
    op.drop_table("currentdatausepreference")
    op.drop_index(op.f("ix_lastservedvendor_vendor"), table_name="lastservedvendor")
    op.drop_index(op.f("ix_lastservedvendor_updated_at"), table_name="lastservedvendor")
    op.drop_index(
        op.f("ix_lastservedvendor_served_notice_history_id"),
        table_name="lastservedvendor",
    )
    op.drop_index(
        op.f("ix_lastservedvendor_provided_identity_id"), table_name="lastservedvendor"
    )
    op.drop_index(
        op.f("ix_lastservedvendor_privacy_notice_id"), table_name="lastservedvendor"
    )
    op.drop_index(
        op.f("ix_lastservedvendor_privacy_notice_history_id"),
        table_name="lastservedvendor",
    )
    op.drop_index(op.f("ix_lastservedvendor_id"), table_name="lastservedvendor")
    op.drop_index(
        op.f("ix_lastservedvendor_fides_user_device_provided_identity_id"),
        table_name="lastservedvendor",
    )
    op.drop_index(op.f("ix_lastservedvendor_created_at"), table_name="lastservedvendor")
    op.drop_table("lastservedvendor")
    op.drop_index(
        op.f("ix_lastservedfeature_updated_at"), table_name="lastservedfeature"
    )
    op.drop_index(
        op.f("ix_lastservedfeature_served_notice_history_id"),
        table_name="lastservedfeature",
    )
    op.drop_index(
        op.f("ix_lastservedfeature_provided_identity_id"),
        table_name="lastservedfeature",
    )
    op.drop_index(
        op.f("ix_lastservedfeature_privacy_notice_id"), table_name="lastservedfeature"
    )
    op.drop_index(
        op.f("ix_lastservedfeature_privacy_notice_history_id"),
        table_name="lastservedfeature",
    )
    op.drop_index(op.f("ix_lastservedfeature_id"), table_name="lastservedfeature")
    op.drop_index(
        op.f("ix_lastservedfeature_fides_user_device_provided_identity_id"),
        table_name="lastservedfeature",
    )
    op.drop_index(op.f("ix_lastservedfeature_feature"), table_name="lastservedfeature")
    op.drop_index(
        op.f("ix_lastservedfeature_created_at"), table_name="lastservedfeature"
    )
    op.drop_table("lastservedfeature")
    op.drop_index(
        op.f("ix_lastserveddatause_updated_at"), table_name="lastserveddatause"
    )
    op.drop_index(
        op.f("ix_lastserveddatause_served_notice_history_id"),
        table_name="lastserveddatause",
    )
    op.drop_index(
        op.f("ix_lastserveddatause_provided_identity_id"),
        table_name="lastserveddatause",
    )
    op.drop_index(
        op.f("ix_lastserveddatause_privacy_notice_id"), table_name="lastserveddatause"
    )
    op.drop_index(
        op.f("ix_lastserveddatause_privacy_notice_history_id"),
        table_name="lastserveddatause",
    )
    op.drop_index(op.f("ix_lastserveddatause_id"), table_name="lastserveddatause")
    op.drop_index(
        op.f("ix_lastserveddatause_fides_user_device_provided_identity_id"),
        table_name="lastserveddatause",
    )
    op.drop_index(op.f("ix_lastserveddatause_data_use"), table_name="lastserveddatause")
    op.drop_index(
        op.f("ix_lastserveddatause_created_at"), table_name="lastserveddatause"
    )
    op.drop_table("lastserveddatause")
    op.drop_index(op.f("ix_tcfdatause_id"), table_name="tcfdatause")
    op.drop_table("tcfdatause")
    # ### end Alembic commands ###
