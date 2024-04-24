"""remove saving preferences for system, vendor, and purpose

Remove these columns and any previous rows where consent was stored against these attributes.
You can no longer save preferences for systems, vendors, and purposes.

Revision ID: 81226042d7d4
Revises: 81886da90395
Create Date: 2023-10-02 00:34:46.828946

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = "81226042d7d4"
down_revision = "81886da90395"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # First let's clean up all rows in currentprivacypreference, lastservednotice, privacypreferencehistory, and servednoticehistory
    # where consent was saved or served against purposes, vendors, or systems
    bind.execute(
        text(
            "DELETE from currentprivacypreference where purpose is not null or vendor is not null or system is not null;"
        )
    )
    bind.execute(
        text(
            "DELETE from lastservednotice where purpose is not null or vendor is not null or system is not null;"
        )
    )
    bind.execute(
        text(
            "DELETE from privacypreferencehistory where purpose is not null or vendor is not null or system is not null;"
        )
    )
    bind.execute(
        text(
            "DELETE from servednoticehistory where purpose is not null or vendor is not null or system is not null;"
        )
    )

    # Drop unique constraints on identities x purpose/system/vendor fields for currentprivacypreference
    op.drop_constraint(
        "fides_user_device_identity_purpose", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "fides_user_device_identity_system", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "fides_user_device_identity_vendor", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint("identity_purpose", "currentprivacypreference", type_="unique")
    op.drop_constraint("identity_system", "currentprivacypreference", type_="unique")
    op.drop_constraint("identity_vendor", "currentprivacypreference", type_="unique")

    # Drop indices on purpose/system/vendor fields for currentprivacypreference

    op.drop_index(
        "ix_currentprivacypreference_purpose", table_name="currentprivacypreference"
    )
    op.drop_index(
        "ix_currentprivacypreference_system", table_name="currentprivacypreference"
    )
    op.drop_index(
        "ix_currentprivacypreference_vendor", table_name="currentprivacypreference"
    )
    # Now delete vendor/purpose/system columns on currentprivacypreference
    op.drop_column("currentprivacypreference", "vendor")
    op.drop_column("currentprivacypreference", "purpose")
    op.drop_column("currentprivacypreference", "system")

    # Remove index on purpose, system, and vendor in lastservednotice table
    op.drop_index("ix_lastservednotice_purpose", table_name="lastservednotice")
    op.drop_index("ix_lastservednotice_system", table_name="lastservednotice")
    op.drop_index("ix_lastservednotice_vendor", table_name="lastservednotice")

    # Drop unique constraints for identities x purpose/system/vendor on lastservednotice table
    op.drop_constraint(
        "last_served_fides_user_device_identity_purpose",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_system",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_vendor",
        "lastservednotice",
        type_="unique",
    )
    op.drop_constraint(
        "last_served_identity_purpose", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_system", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_identity_vendor", "lastservednotice", type_="unique"
    )
    # Now we can drop the columns for vendor/purpose/system on lastservednotice table
    op.drop_column("lastservednotice", "vendor")
    op.drop_column("lastservednotice", "purpose")
    op.drop_column("lastservednotice", "system")

    # Drop indices for purpose/system/vendor on privacypreferencehistory table
    op.drop_index(
        "ix_privacypreferencehistory_purpose", table_name="privacypreferencehistory"
    )
    op.drop_index(
        "ix_privacypreferencehistory_system", table_name="privacypreferencehistory"
    )
    op.drop_index(
        "ix_privacypreferencehistory_vendor", table_name="privacypreferencehistory"
    )
    # Now we can drop system/vendor/purpose columns on privacypreferencehistory
    op.drop_column("privacypreferencehistory", "system")
    op.drop_column("privacypreferencehistory", "purpose")
    op.drop_column("privacypreferencehistory", "vendor")

    # Drop indices for purpose/system/vendor on servednoticehistory table
    op.drop_index("ix_servednoticehistory_purpose", table_name="servednoticehistory")
    op.drop_index("ix_servednoticehistory_system", table_name="servednoticehistory")
    op.drop_index("ix_servednoticehistory_vendor", table_name="servednoticehistory")

    # Now we can drop system/purpose/vendor columns on servednoticehistory table
    op.drop_column("servednoticehistory", "system")
    op.drop_column("servednoticehistory", "purpose")
    op.drop_column("servednoticehistory", "vendor")


def downgrade():
    op.add_column(
        "servednoticehistory",
        sa.Column("vendor", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("purpose", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("system", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_servednoticehistory_vendor", "servednoticehistory", ["vendor"], unique=False
    )
    op.create_index(
        "ix_servednoticehistory_system", "servednoticehistory", ["system"], unique=False
    )
    op.create_index(
        "ix_servednoticehistory_purpose",
        "servednoticehistory",
        ["purpose"],
        unique=False,
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("vendor", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("purpose", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("system", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_privacypreferencehistory_vendor",
        "privacypreferencehistory",
        ["vendor"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_system",
        "privacypreferencehistory",
        ["system"],
        unique=False,
    )
    op.create_index(
        "ix_privacypreferencehistory_purpose",
        "privacypreferencehistory",
        ["purpose"],
        unique=False,
    )
    op.add_column(
        "lastservednotice",
        sa.Column("system", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "lastservednotice",
        sa.Column("purpose", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "lastservednotice",
        sa.Column("vendor", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_unique_constraint(
        "last_served_identity_vendor",
        "lastservednotice",
        ["provided_identity_id", "vendor"],
    )
    op.create_unique_constraint(
        "last_served_identity_system",
        "lastservednotice",
        ["provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "last_served_identity_purpose",
        "lastservednotice",
        ["provided_identity_id", "purpose"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_vendor",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "vendor"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_system",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_purpose",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "purpose"],
    )
    op.create_index(
        "ix_lastservednotice_vendor", "lastservednotice", ["vendor"], unique=False
    )
    op.create_index(
        "ix_lastservednotice_system", "lastservednotice", ["system"], unique=False
    )
    op.create_index(
        "ix_lastservednotice_purpose", "lastservednotice", ["purpose"], unique=False
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("system", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("purpose", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "currentprivacypreference",
        sa.Column("vendor", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_currentprivacypreference_vendor",
        "currentprivacypreference",
        ["vendor"],
        unique=False,
    )
    op.create_index(
        "ix_currentprivacypreference_system",
        "currentprivacypreference",
        ["system"],
        unique=False,
    )
    op.create_index(
        "ix_currentprivacypreference_purpose",
        "currentprivacypreference",
        ["purpose"],
        unique=False,
    )
    op.create_unique_constraint(
        "identity_vendor",
        "currentprivacypreference",
        ["provided_identity_id", "vendor"],
    )
    op.create_unique_constraint(
        "identity_system",
        "currentprivacypreference",
        ["provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "identity_purpose",
        "currentprivacypreference",
        ["provided_identity_id", "purpose"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_vendor",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "vendor"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_system",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "system"],
    )
    op.create_unique_constraint(
        "fides_user_device_identity_purpose",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "purpose"],
    )
