"""Add tcf columns

Revision ID: 66df7d9b8103
Revises: 192f23f4c968
Create Date: 2023-08-23 21:12:43.651877

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "66df7d9b8103"
down_revision = "192f23f4c968"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "consentsettings",
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
        sa.Column("tcf_enabled", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_consentsettings_id"), "consentsettings", ["id"], unique=False
    )
    op.add_column(
        "currentprivacypreference", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    op.add_column(
        "currentprivacypreference", sa.Column("feature", sa.Integer(), nullable=True)
    )
    op.add_column(
        "currentprivacypreference", sa.Column("purpose", sa.Integer(), nullable=True)
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("special_feature", sa.Integer(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("special_purpose", sa.Integer(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference", sa.Column("vendor", sa.String(), nullable=True)
    )
    op.add_column(
        "currentprivacypreference", sa.Column("system", sa.String(), nullable=True)
    )
    op.alter_column(
        "currentprivacypreference",
        "privacy_notice_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        "currentprivacypreference",
        "privacy_notice_history_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_unique_constraint(
        "fides_user_device_identity_feature",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "feature"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_purpose",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "purpose"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_special_feature",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "special_feature"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_special_purpose",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "special_purpose"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_system",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_vendor",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "vendor"],
    )
    op.create_unique_constraint(
        "identity_feature",
        "currentprivacypreference",
        ["provided_identity_id", "feature"],
    )
    op.create_unique_constraint(
        "identity_purpose",
        "currentprivacypreference",
        ["provided_identity_id", "purpose"],
    )
    op.create_unique_constraint(
        "identity_special_feature",
        "currentprivacypreference",
        ["provided_identity_id", "special_feature"],
    )
    op.create_unique_constraint(
        "identity_special_purpose",
        "currentprivacypreference",
        ["provided_identity_id", "purpose"],
    )
    op.create_unique_constraint(
        "identity_system",
        "currentprivacypreference",
        ["provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "identity_vendor",
        "currentprivacypreference",
        ["provided_identity_id", "vendor"],
    )
    op.create_index(
        op.f("ix_currentprivacypreference_feature"),
        "currentprivacypreference",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_purpose"),
        "currentprivacypreference",
        ["purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_special_feature"),
        "currentprivacypreference",
        ["special_feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_special_purpose"),
        "currentprivacypreference",
        ["special_purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_system"),
        "currentprivacypreference",
        ["system"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_vendor"),
        "currentprivacypreference",
        ["vendor"],
        unique=False,
    )
    op.add_column(
        "lastservednotice", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    op.add_column("lastservednotice", sa.Column("feature", sa.Integer(), nullable=True))
    op.add_column("lastservednotice", sa.Column("purpose", sa.Integer(), nullable=True))
    op.add_column(
        "lastservednotice", sa.Column("special_feature", sa.Integer(), nullable=True)
    )
    op.add_column(
        "lastservednotice", sa.Column("special_purpose", sa.Integer(), nullable=True)
    )
    op.add_column("lastservednotice", sa.Column("vendor", sa.String(), nullable=True))
    op.add_column("lastservednotice", sa.Column("system", sa.String(), nullable=True))
    op.alter_column(
        "lastservednotice",
        "privacy_notice_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        "lastservednotice",
        "privacy_notice_history_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_index(
        op.f("ix_lastservednotice_feature"),
        "lastservednotice",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_purpose"),
        "lastservednotice",
        ["purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_special_feature"),
        "lastservednotice",
        ["special_feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_special_purpose"),
        "lastservednotice",
        ["special_purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_system"), "lastservednotice", ["system"], unique=False
    )
    op.create_index(
        op.f("ix_lastservednotice_vendor"), "lastservednotice", ["vendor"], unique=False
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_feature",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "feature"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_purpose",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "purpose"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_special_feature",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "special_feature"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_special_purpose",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "special_purpose"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_system",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_vendor",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "vendor"],
    )
    op.create_unique_constraint(
        "last_served_identity_feature",
        "lastservednotice",
        ["provided_identity_id", "feature"],
    )
    op.create_unique_constraint(
        "last_served_identity_purpose",
        "lastservednotice",
        ["provided_identity_id", "purpose"],
    )
    op.create_unique_constraint(
        "last_served_identity_special_feature",
        "lastservednotice",
        ["provided_identity_id", "special_feature"],
    )
    op.create_unique_constraint(
        "last_served_identity_special_purpose",
        "lastservednotice",
        ["provided_identity_id", "special_purpose"],
    )
    op.create_unique_constraint(
        "last_served_identity_system",
        "lastservednotice",
        ["provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "last_served_identity_vendor",
        "lastservednotice",
        ["provided_identity_id", "vendor"],
    )
    op.drop_index("ix_messagingtemplate_id", table_name="messaging_template")
    op.drop_index("ix_messagingtemplate_key", table_name="messaging_template")
    op.create_index(
        op.f("ix_messaging_template_id"), "messaging_template", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_messaging_template_key"), "messaging_template", ["key"], unique=True
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("feature", sa.Integer(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("purpose", sa.Integer(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("special_feature", sa.Integer(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("special_purpose", sa.Integer(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("vendor", sa.String(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("system", sa.String(), nullable=True)
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    op.alter_column(
        "privacypreferencehistory",
        "privacy_notice_history_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_feature"),
        "privacypreferencehistory",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_purpose"),
        "privacypreferencehistory",
        ["purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_special_feature"),
        "privacypreferencehistory",
        ["special_feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_special_purpose"),
        "privacypreferencehistory",
        ["special_purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_system"),
        "privacypreferencehistory",
        ["system"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_vendor"),
        "privacypreferencehistory",
        ["vendor"],
        unique=False,
    )
    op.add_column(
        "servednoticehistory", sa.Column("feature", sa.Integer(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("purpose", sa.Integer(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("special_feature", sa.Integer(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("special_purpose", sa.Integer(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("vendor", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("system", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    op.alter_column(
        "servednoticehistory",
        "privacy_notice_history_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_index(
        op.f("ix_servednoticehistory_feature"),
        "servednoticehistory",
        ["feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_purpose"),
        "servednoticehistory",
        ["purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_special_feature"),
        "servednoticehistory",
        ["special_feature"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_special_purpose"),
        "servednoticehistory",
        ["special_purpose"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_system"),
        "servednoticehistory",
        ["system"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_vendor"),
        "servednoticehistory",
        ["vendor"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_servednoticehistory_vendor"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_system"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_special_purpose"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_special_feature"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_purpose"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_feature"), table_name="servednoticehistory"
    )
    op.drop_column("servednoticehistory", "tcf_version")
    op.drop_column("servednoticehistory", "system")
    op.drop_column("servednoticehistory", "vendor")
    op.drop_column("servednoticehistory", "special_purpose")
    op.drop_column("servednoticehistory", "special_feature")
    op.drop_column("servednoticehistory", "purpose")
    op.drop_column("servednoticehistory", "feature")
    op.drop_index(
        op.f("ix_privacypreferencehistory_vendor"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_system"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_special_purpose"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_special_feature"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_purpose"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_feature"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "tcf_version")
    op.drop_column("privacypreferencehistory", "system")
    op.drop_column("privacypreferencehistory", "vendor")
    op.drop_column("privacypreferencehistory", "special_purpose")
    op.drop_column("privacypreferencehistory", "special_feature")
    op.drop_column("privacypreferencehistory", "purpose")
    op.drop_column("privacypreferencehistory", "feature")
    op.drop_index(op.f("ix_messaging_template_key"), table_name="messaging_template")
    op.drop_index(op.f("ix_messaging_template_id"), table_name="messaging_template")
    op.create_index(
        "ix_messagingtemplate_key", "messaging_template", ["key"], unique=False
    )
    op.create_index(
        "ix_messagingtemplate_id", "messaging_template", ["id"], unique=False
    )
    op.drop_constraint(
        "last_served_identity_vendor", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_system", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_special_purpose", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_special_feature", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_purpose", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_feature", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_vendor",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_system",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_special_purpose",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_special_feature",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_purpose",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_feature",
        "lastservednotice",
        type_="unique",
    )
    op.drop_index(op.f("ix_lastservednotice_vendor"), table_name="lastservednotice")
    op.drop_index(op.f("ix_lastservednotice_system"), table_name="lastservednotice")
    op.drop_index(
        op.f("ix_lastservednotice_special_purpose"), table_name="lastservednotice"
    )
    op.drop_index(
        op.f("ix_lastservednotice_special_feature"), table_name="lastservednotice"
    )
    op.drop_index(op.f("ix_lastservednotice_purpose"), table_name="lastservednotice")
    op.drop_index(op.f("ix_lastservednotice_feature"), table_name="lastservednotice")
    op.drop_column("lastservednotice", "system")
    op.drop_column("lastservednotice", "vendor")
    op.drop_column("lastservednotice", "special_purpose")
    op.drop_column("lastservednotice", "special_feature")
    op.drop_column("lastservednotice", "purpose")
    op.drop_column("lastservednotice", "feature")
    op.drop_column("lastservednotice", "tcf_version")
    op.drop_index(
        op.f("ix_currentprivacypreference_vendor"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_system"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_special_purpose"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_special_feature"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_purpose"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_feature"),
        table_name="currentprivacypreference",
    )
    op.drop_constraint("identity_vendor", "currentprivacypreference", type_="unique")
    op.drop_constraint("identity_system", "currentprivacypreference", type_="unique")
    op.drop_constraint(
        "identity_special_purpose", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "identity_special_feature", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint("identity_purpose", "currentprivacypreference", type_="unique")
    op.drop_constraint("identity_feature", "currentprivacypreference", type_="unique")
    op.drop_constraint(
        "fides_user_device_identity_vendor", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "fides_user_device_identity_system", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "fides_user_device_identity_special_purpose",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_constraint(
        "fides_user_device_identity_special_feature",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_constraint(
        "fides_user_device_identity_purpose", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "fides_user_device_identity_feature", "currentprivacypreference", type_="unique"
    )
    op.drop_column("currentprivacypreference", "system")
    op.drop_column("currentprivacypreference", "vendor")
    op.drop_column("currentprivacypreference", "special_purpose")
    op.drop_column("currentprivacypreference", "special_feature")
    op.drop_column("currentprivacypreference", "purpose")
    op.drop_column("currentprivacypreference", "feature")
    op.drop_column("currentprivacypreference", "tcf_version")
    op.drop_index(op.f("ix_consentsettings_id"), table_name="consentsettings")
    op.drop_table("consentsettings")
