"""add tcf columns

Revision ID: 66df7d9b8103
Revises: fd52d5f08c17
Create Date: 2023-07-24 20:23:49.622518

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "66df7d9b8103"
down_revision = "fd52d5f08c17"
branch_labels = None
depends_on = None


def upgrade():
    # Add new consent settings table
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

    # Allow current privacy preferences to be saved against a purpose, special purpose, vendor, feature, or special feature
    op.add_column(
        "currentprivacypreference", sa.Column("purpose", sa.Integer(), nullable=True)
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("special_purpose", sa.Integer(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference", sa.Column("vendor", sa.String(), nullable=True)
    )
    op.add_column(
        "currentprivacypreference", sa.Column("feature", sa.Integer(), nullable=True)
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("special_feature", sa.Integer(), nullable=True),
    )
    # Add TCF version for historical record keeping
    op.add_column(
        "currentprivacypreference", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    # Relax nullable constraint on privacy notice id and history id since we can save against tcf attributes instead
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
    # Create unique constraints in CurrentPrivacyPreference for both possible identity types and
    # every feature/special feature/vendor/purpose/special purpose
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
        "identity_vendor",
        "currentprivacypreference",
        ["provided_identity_id", "vendor"],
    )
    # Index Current Privacy Preference feature, purpose, special feature, special purpose, and vendor
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
        op.f("ix_currentprivacypreference_vendor"),
        "currentprivacypreference",
        ["vendor"],
        unique=False,
    )

    # Allow last served notice to be saved for a given feature, purpose, special feature, special purpose, or vendor.
    # Also track tcf_version fo record keeping
    op.add_column("lastservednotice", sa.Column("feature", sa.Integer(), nullable=True))
    op.add_column("lastservednotice", sa.Column("purpose", sa.Integer(), nullable=True))
    op.add_column(
        "lastservednotice", sa.Column("special_feature", sa.Integer(), nullable=True)
    )
    op.add_column(
        "lastservednotice", sa.Column("special_purpose", sa.Integer(), nullable=True)
    )
    op.add_column(
        "lastservednotice", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    op.add_column("lastservednotice", sa.Column("vendor", sa.String(), nullable=True))
    # Relax not nullable constraint for privacy notice and privacy notice history now that
    # we can save last serve against TCF attributes alternatively
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
    # Index last served feature/purpose/special feature/special purpose/vendor
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
        op.f("ix_lastservednotice_vendor"), "lastservednotice", ["vendor"], unique=False
    )
    # Add unique constraints for last served for both identity types and all tcf attribute types
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
        "last_served_identity_vendor",
        "lastservednotice",
        ["provided_identity_id", "vendor"],
    )
    # Add feature, purpose, special feature, special purpose, and vendor for PrivacyPreferenceHistory
    # This allows preferences to be saved against TCF attributes directly.  Also track tcf_version for record keeping
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
        "privacypreferencehistory", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    # Relax privacy notice history id since we can save privacy preference history against tcf attributes
    op.alter_column(
        "privacypreferencehistory",
        "privacy_notice_history_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    # Index privacy preference history feature, purpose, special feature, special purpose, and vendor
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
        op.f("ix_privacypreferencehistory_vendor"),
        "privacypreferencehistory",
        ["vendor"],
        unique=False,
    )
    # For served notice history, start tracking optional feature, purpose, special feature,
    # special purpose, vendor, and tcf_version
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
        "servednoticehistory", sa.Column("tcf_version", sa.String(), nullable=True)
    )
    # Relax privacy notice history id on served notice history id
    op.alter_column(
        "servednoticehistory",
        "privacy_notice_history_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    # Index feature, purpose, special feature, special purpose, and vendor on served notice history
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
    op.drop_column("privacypreferencehistory", "vendor")
    op.drop_column("privacypreferencehistory", "special_purpose")
    op.drop_column("privacypreferencehistory", "special_feature")
    op.drop_column("privacypreferencehistory", "purpose")
    op.drop_column("privacypreferencehistory", "feature")
    op.drop_constraint(
        "last_served_identity_vendor", "lastservednotice", type_="unique"
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
    op.drop_index(
        op.f("ix_lastservednotice_special_purpose"), table_name="lastservednotice"
    )
    op.drop_index(
        op.f("ix_lastservednotice_special_feature"), table_name="lastservednotice"
    )
    op.drop_index(op.f("ix_lastservednotice_purpose"), table_name="lastservednotice")
    op.drop_index(op.f("ix_lastservednotice_feature"), table_name="lastservednotice")

    op.drop_column("lastservednotice", "vendor")
    op.drop_column("lastservednotice", "tcf_version")
    op.drop_column("lastservednotice", "special_purpose")
    op.drop_column("lastservednotice", "special_feature")
    op.drop_column("lastservednotice", "purpose")
    op.drop_column("lastservednotice", "feature")
    op.drop_index(
        op.f("ix_currentprivacypreference_vendor"),
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

    op.drop_column("currentprivacypreference", "vendor")
    op.drop_column("currentprivacypreference", "tcf_version")
    op.drop_column("currentprivacypreference", "special_purpose")
    op.drop_column("currentprivacypreference", "special_feature")
    op.drop_column("currentprivacypreference", "purpose")
    op.drop_column("currentprivacypreference", "feature")
    op.drop_index(op.f("ix_consentsettings_id"), table_name="consentsettings")
    op.drop_table("consentsettings")
