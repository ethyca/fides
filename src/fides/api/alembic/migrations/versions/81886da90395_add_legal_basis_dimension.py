"""add legal basis dimension

We've previously been saving preferences against purposes, vendors, and systems, but we
need to instead save preferences against a purpose/vendor AND a legal basis.

Revision ID: 81886da90395
Revises: 9b98aba5bba8
Create Date: 2023-09-30 17:39:46.251444

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "81886da90395"
down_revision = "9b98aba5bba8"
branch_labels = None
depends_on = None


def upgrade():
    # Add six new columns to currentprivacypreference table for purpose/system/vendor x 2 legal bases
    op.add_column(
        "currentprivacypreference",
        sa.Column("purpose_consent", sa.Integer(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("purpose_legitimate_interests", sa.Integer(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("vendor_consent", sa.String(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("vendor_legitimate_interests", sa.String(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("system_consent", sa.String(), nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("system_legitimate_interests", sa.String(), nullable=True),
    )
    # Add 12 unique constraints - 3 new columns x 2 legal bases 2 x 2 identity types
    op.create_unique_constraint(
        "fides_user_device_identity_purpose_consent",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "purpose_consent"],
    )

    op.create_unique_constraint(
        "fides_user_device_identity_purpose_leg_interests",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "purpose_legitimate_interests"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_system_consent",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "system_consent"],
    )

    op.create_unique_constraint(
        "fides_user_device_identity_system_leg_interests",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "system_legitimate_interests"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_vendor_consent",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "vendor_consent"],
    )

    op.create_unique_constraint(
        "fides_user_device_identity_vendor_leg_interests",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "vendor_legitimate_interests"],
    )
    op.create_unique_constraint(
        "identity_purpose_consent",
        "currentprivacypreference",
        ["provided_identity_id", "purpose_consent"],
    )

    op.create_unique_constraint(
        "identity_purpose_leg_interests",
        "currentprivacypreference",
        ["provided_identity_id", "purpose_legitimate_interests"],
    )

    op.create_unique_constraint(
        "identity_system_consent",
        "currentprivacypreference",
        ["provided_identity_id", "system_consent"],
    )
    op.create_unique_constraint(
        "identity_system_leg_interests",
        "currentprivacypreference",
        ["provided_identity_id", "system_legitimate_interests"],
    )

    op.create_unique_constraint(
        "identity_vendor_consent",
        "currentprivacypreference",
        ["provided_identity_id", "vendor_consent"],
    )
    op.create_unique_constraint(
        "identity_vendor_leg_interests",
        "currentprivacypreference",
        ["provided_identity_id", "vendor_legitimate_interests"],
    )

    # Add six new indices - for purpose/vendor/system columns x 2 legal bases
    op.create_index(
        op.f("ix_currentprivacypreference_purpose_consent"),
        "currentprivacypreference",
        ["purpose_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_purpose_legitimate_interests"),
        "currentprivacypreference",
        ["purpose_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_system_consent"),
        "currentprivacypreference",
        ["system_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_system_legitimate_interests"),
        "currentprivacypreference",
        ["system_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_vendor_consent"),
        "currentprivacypreference",
        ["vendor_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_vendor_legitimate_interests"),
        "currentprivacypreference",
        ["vendor_legitimate_interests"],
        unique=False,
    )
    # Add six new columns to lastservednotice for purpose, vendor, and consent x 2 legal bases
    op.add_column(
        "lastservednotice", sa.Column("purpose_consent", sa.Integer(), nullable=True)
    )
    op.add_column(
        "lastservednotice",
        sa.Column("purpose_legitimate_interests", sa.Integer(), nullable=True),
    )
    op.add_column(
        "lastservednotice", sa.Column("vendor_consent", sa.String(), nullable=True)
    )
    op.add_column(
        "lastservednotice",
        sa.Column("vendor_legitimate_interests", sa.String(), nullable=True),
    )
    op.add_column(
        "lastservednotice", sa.Column("system_consent", sa.String(), nullable=True)
    )
    op.add_column(
        "lastservednotice",
        sa.Column("system_legitimate_interests", sa.String(), nullable=True),
    )
    # Add six new indices to lastservednotice for purpose, vendor, and consent x 2 legal bases

    op.create_index(
        op.f("ix_lastservednotice_purpose_consent"),
        "lastservednotice",
        ["purpose_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_purpose_legitimate_interests"),
        "lastservednotice",
        ["purpose_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_system_consent"),
        "lastservednotice",
        ["system_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_system_legitimate_interests"),
        "lastservednotice",
        ["system_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_vendor_consent"),
        "lastservednotice",
        ["vendor_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednotice_vendor_legitimate_interests"),
        "lastservednotice",
        ["vendor_legitimate_interests"],
        unique=False,
    )
    # Add 12 unique constraints to lastserved notice - purpose/vendor/system x 2 legal bases x 2 identity types
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_purpose_consent",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "purpose_consent"],
    )

    op.create_unique_constraint(
        "last_served_fides_user_device_identity_purpose_leg_interests",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "purpose_legitimate_interests"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_system_consent",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "system_consent"],
    )

    op.create_unique_constraint(
        "last_served_fides_user_device_identity_system_leg_interests",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "system_legitimate_interests"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_vendor_consent",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "vendor_consent"],
    )

    op.create_unique_constraint(
        "last_served_fides_user_device_identity_vendor_leg_interests",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "vendor_legitimate_interests"],
    )
    op.create_unique_constraint(
        "last_served_identity_purpose_consent",
        "lastservednotice",
        ["provided_identity_id", "purpose_consent"],
    )
    op.create_unique_constraint(
        "last_served_identity_purpose_legitimate_interests",
        "lastservednotice",
        ["provided_identity_id", "purpose_legitimate_interests"],
    )

    op.create_unique_constraint(
        "last_served_identity_system_consent",
        "lastservednotice",
        ["provided_identity_id", "system_consent"],
    )
    op.create_unique_constraint(
        "last_served_identity_system_leg_interests",
        "lastservednotice",
        ["provided_identity_id", "system_legitimate_interests"],
    )

    op.create_unique_constraint(
        "last_served_identity_vendor_consent",
        "lastservednotice",
        ["provided_identity_id", "vendor_consent"],
    )
    op.create_unique_constraint(
        "last_served_identity_vendor_leg_interests",
        "lastservednotice",
        ["provided_identity_id", "vendor_legitimate_interests"],
    )

    # Add six new columns to privacypreferencehistory - purpose/vendor/system x 2 legal bases
    op.add_column(
        "privacypreferencehistory",
        sa.Column("purpose_consent", sa.Integer(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("purpose_legitimate_interests", sa.Integer(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("vendor_consent", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("vendor_legitimate_interests", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("system_consent", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("system_legitimate_interests", sa.String(), nullable=True),
    )
    # Add six indices to privacypreference history - purpose/vendor/system x 2 legal bases
    op.create_index(
        op.f("ix_privacypreferencehistory_purpose_consent"),
        "privacypreferencehistory",
        ["purpose_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_purpose_legitimate_interests"),
        "privacypreferencehistory",
        ["purpose_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_system_consent"),
        "privacypreferencehistory",
        ["system_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_system_legitimate_interests"),
        "privacypreferencehistory",
        ["system_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_vendor_consent"),
        "privacypreferencehistory",
        ["vendor_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_vendor_legitimate_interests"),
        "privacypreferencehistory",
        ["vendor_legitimate_interests"],
        unique=False,
    )
    # Add six new columns to servednoticehistory
    op.add_column(
        "servednoticehistory", sa.Column("purpose_consent", sa.Integer(), nullable=True)
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("purpose_legitimate_interests", sa.Integer(), nullable=True),
    )
    op.add_column(
        "servednoticehistory", sa.Column("vendor_consent", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("vendor_legitimate_interests", sa.String(), nullable=True),
    )
    op.add_column(
        "servednoticehistory", sa.Column("system_consent", sa.String(), nullable=True)
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("system_legitimate_interests", sa.String(), nullable=True),
    )
    # Add six new indices to servednoticehistory
    op.create_index(
        op.f("ix_servednoticehistory_purpose_consent"),
        "servednoticehistory",
        ["purpose_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_purpose_legitimate_interests"),
        "servednoticehistory",
        ["purpose_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_system_consent"),
        "servednoticehistory",
        ["system_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_system_legitimate_interests"),
        "servednoticehistory",
        ["system_legitimate_interests"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_vendor_consent"),
        "servednoticehistory",
        ["vendor_consent"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistory_vendor_legitimate_interests"),
        "servednoticehistory",
        ["vendor_legitimate_interests"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_servednoticehistory_vendor_legitimate_interests"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_vendor_consent"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_system_legitimate_interests"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_system_consent"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_servednoticehistory_purpose_legitimate_interests"),
        table_name="servednoticehistory",
    )
    op.drop_index(
        op.f("ix_servednoticehistory_purpose_consent"), table_name="servednoticehistory"
    )
    op.drop_column("servednoticehistory", "system_legitimate_interests")
    op.drop_column("servednoticehistory", "system_consent")
    op.drop_column("servednoticehistory", "vendor_legitimate_interests")
    op.drop_column("servednoticehistory", "vendor_consent")
    op.drop_column("servednoticehistory", "purpose_legitimate_interests")
    op.drop_column("servednoticehistory", "purpose_consent")
    op.drop_index(
        op.f("ix_privacypreferencehistory_vendor_legitimate_interests"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_vendor_consent"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_system_legitimate_interests"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_system_consent"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_purpose_legitimate_interests"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_purpose_consent"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "system_legitimate_interests")
    op.drop_column("privacypreferencehistory", "system_consent")
    op.drop_column("privacypreferencehistory", "vendor_legitimate_interests")
    op.drop_column("privacypreferencehistory", "vendor_consent")
    op.drop_column("privacypreferencehistory", "purpose_legitimate_interests")
    op.drop_column("privacypreferencehistory", "purpose_consent")
    op.drop_constraint(
        "last_served_identity_vendor_consent", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_vendor_leg_interests", "lastservednotice", type_="unique"
    )

    op.drop_constraint(
        "last_served_identity_system_consent", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_system_leg_interests", "lastservednotice", type_="unique"
    )

    op.drop_constraint(
        "last_served_identity_purpose_consent", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_purpose_legitimate_interests",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_vendor_consent",
        "lastservednotice",
        type_="unique",
    )

    op.drop_constraint(
        "last_served_fides_user_device_identity_vendor_leg_interests",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_system_consent",
        "lastservednotice",
        type_="unique",
    )

    op.drop_constraint(
        "last_served_fides_user_device_identity_system_leg_interests",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_purpose_consent",
        "lastservednotice",
        type_="unique",
    )

    op.drop_constraint(
        "last_served_fides_user_device_identity_purpose_leg_interests",
        "lastservednotice",
        type_="unique",
    )
    op.drop_index(
        op.f("ix_lastservednotice_vendor_legitimate_interests"),
        table_name="lastservednotice",
    )
    op.drop_index(
        op.f("ix_lastservednotice_vendor_consent"), table_name="lastservednotice"
    )
    op.drop_index(
        op.f("ix_lastservednotice_system_legitimate_interests"),
        table_name="lastservednotice",
    )
    op.drop_index(
        op.f("ix_lastservednotice_system_consent"), table_name="lastservednotice"
    )
    op.drop_index(
        op.f("ix_lastservednotice_purpose_legitimate_interests"),
        table_name="lastservednotice",
    )
    op.drop_index(
        op.f("ix_lastservednotice_purpose_consent"), table_name="lastservednotice"
    )
    op.drop_column("lastservednotice", "system_legitimate_interests")
    op.drop_column("lastservednotice", "system_consent")
    op.drop_column("lastservednotice", "vendor_legitimate_interests")
    op.drop_column("lastservednotice", "vendor_consent")
    op.drop_column("lastservednotice", "purpose_legitimate_interests")
    op.drop_column("lastservednotice", "purpose_consent")
    op.drop_index(
        op.f("ix_currentprivacypreference_vendor_legitimate_interests"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_vendor_consent"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_system_legitimate_interests"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_system_consent"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_purpose_legitimate_interests"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_purpose_consent"),
        table_name="currentprivacypreference",
    )
    op.drop_constraint(
        "identity_vendor_consent", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "identity_vendor_leg_interests", "currentprivacypreference", type_="unique"
    )

    op.drop_constraint(
        "identity_system_consent", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "identity_system_leg_interests", "currentprivacypreference", type_="unique"
    )

    op.drop_constraint(
        "identity_purpose_consent", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "identity_purpose_leg_interests", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "fides_user_device_identity_vendor_consent",
        "currentprivacypreference",
        type_="unique",
    )

    op.drop_constraint(
        "fides_user_device_identity_vendor_leg_interests",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_constraint(
        "fides_user_device_identity_system_consent",
        "currentprivacypreference",
        type_="unique",
    )

    op.drop_constraint(
        "fides_user_device_identity_system_leg_interests",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_constraint(
        "fides_user_device_identity_purpose_consent",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_constraint(
        "fides_user_device_identity_purpose_leg_interests",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_column("currentprivacypreference", "system_legitimate_interests")
    op.drop_column("currentprivacypreference", "system_consent")
    op.drop_column("currentprivacypreference", "vendor_legitimate_interests")
    op.drop_column("currentprivacypreference", "vendor_consent")
    op.drop_column("currentprivacypreference", "purpose_legitimate_interests")
    op.drop_column("currentprivacypreference", "purpose_consent")
