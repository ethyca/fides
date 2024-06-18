"""add external id to privacy preference

Revision ID: 5fe01e730171
Revises: 5f96f13be8ec
Create Date: 2024-05-31 17:11:50.566937

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "5fe01e730171"
down_revision = "5f96f13be8ec"
branch_labels = None
depends_on = None

"""
WARNING - Conditional migration based on table size

This migration script checks the size of specific tables and performs the following actions:

1. If the tables have less than 1 million rows:
   - Creates the necessary indices
   - Adds the required constraints

2. If the tables are too large (1 million rows or more):
   - Logs non-blocking SQL commands to create the indices and constraints
   - The non-blocking commands utilize:
     - `CREATE INDEX CONCURRENTLY` for creating indices
     - `ADD CONSTRAINT USING INDEX` for adding constraints
   - These commands add the indices and constraints without blocking any reads or writes on the tables
"""


def upgrade():
    op.add_column(
        "consentrequest",
        sa.Column("property_id", sa.String(), nullable=True),
    )
    op.add_column(
        "currentprivacypreferencev2",
        sa.Column(
            "external_id",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "currentprivacypreferencev2",
        sa.Column("hashed_external_id", sa.String(), nullable=True),
    )
    op.add_column(
        "currentprivacypreferencev2",
        sa.Column("property_id", sa.String(), nullable=True),
    )
    op.drop_constraint(
        "last_saved_for_email", "currentprivacypreferencev2", type_="unique"
    )
    op.drop_constraint(
        "last_saved_for_fides_user_device", "currentprivacypreferencev2", type_="unique"
    )
    op.drop_constraint(
        "last_saved_for_phone_number", "currentprivacypreferencev2", type_="unique"
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "external_id",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("hashed_external_id", sa.String(), nullable=True),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column(
            "external_id",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("hashed_external_id", sa.String(), nullable=True),
    )

    connection = op.get_bind()

    currentprivacypreferencev2_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM currentprivacypreferencev2")
    ).scalar()
    if currentprivacypreferencev2_count < 1000000:
        op.create_index(
            op.f("ix_currentprivacypreferencev2_hashed_external_id"),
            "currentprivacypreferencev2",
            ["hashed_external_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_currentprivacypreferencev2_email_property_id"),
            "currentprivacypreferencev2",
            ["email", "property_id"],
            unique=True,
        )
        op.create_index(
            op.f("ix_currentprivacypreferencev2_external_id_property_id"),
            "currentprivacypreferencev2",
            ["external_id", "property_id"],
            unique=True,
        )
        op.create_index(
            op.f("ix_currentprivacypreferencev2_fides_user_device_property_id"),
            "currentprivacypreferencev2",
            ["fides_user_device", "property_id"],
            unique=True,
        )
        op.create_index(
            op.f("ix_currentprivacypreferencev2_phone_number_property_id"),
            "currentprivacypreferencev2",
            ["phone_number", "property_id"],
            unique=True,
        )
        op.execute(
            """
            ALTER TABLE currentprivacypreferencev2
            ADD CONSTRAINT last_saved_for_email_per_property_id
            UNIQUE USING INDEX ix_currentprivacypreferencev2_email_property_id;
            """
        )
        op.execute(
            """
            ALTER TABLE currentprivacypreferencev2
            ADD CONSTRAINT last_saved_for_external_id_per_property_id
            UNIQUE USING INDEX ix_currentprivacypreferencev2_external_id_property_id;
            """
        )
        op.execute(
            """
            ALTER TABLE currentprivacypreferencev2
            ADD CONSTRAINT last_saved_for_fides_user_device_per_property_id
            UNIQUE USING INDEX ix_currentprivacypreferencev2_fides_user_device_property_id;
            """
        )
        op.execute(
            """
            ALTER TABLE currentprivacypreferencev2
            ADD CONSTRAINT last_saved_for_phone_number_per_property_id
            UNIQUE USING INDEX ix_currentprivacypreferencev2_phone_number_property_id;
            """
        )
    else:
        logger.warning(
            "The currentprivacypreferencev2 table has more than 1 million rows, "
            "skipping index and constraint creation. Be sure to manually run the following commands:\n"
            "- 'CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_email_property_id "
            "ON currentprivacypreferencev2 (email, property_id)'\n"
            "- 'CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_external_id_property_id "
            "ON currentprivacypreferencev2 (external_id, property_id)'\n"
            "- 'CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_fides_user_device_property_id "
            "ON currentprivacypreferencev2 (fides_user_device, property_id)'\n"
            "- 'CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_phone_number_property_id "
            "ON currentprivacypreferencev2 (phone_number, property_id)'\n"
            "- 'CREATE INDEX CONCURRENTLY ix_currentprivacypreferencev2_hashed_external_id "
            "ON currentprivacypreferencev2 (hashed_external_id)'\n"
            "- 'ALTER TABLE currentprivacypreferencev2 "
            "ADD CONSTRAINT last_saved_for_email_per_property_id "
            "UNIQUE USING INDEX ix_currentprivacypreferencev2_email_property_id'\n"
            "- 'ALTER TABLE currentprivacypreferencev2 "
            "ADD CONSTRAINT last_saved_for_external_id_per_property_id "
            "UNIQUE USING INDEX ix_currentprivacypreferencev2_external_id_property_id'\n"
            "- 'ALTER TABLE currentprivacypreferencev2 "
            "ADD CONSTRAINT last_saved_for_fides_user_device_per_property_id "
            "UNIQUE USING INDEX ix_currentprivacypreferencev2_fides_user_device_property_id'\n"
            "- 'ALTER TABLE currentprivacypreferencev2 "
            "ADD CONSTRAINT last_saved_for_phone_number_per_property_id "
            "UNIQUE USING INDEX ix_currentprivacypreferencev2_phone_number_property_id'"
        )

    privacypreferencehistory_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM privacypreferencehistory")
    ).scalar()

    if privacypreferencehistory_count < 1000000:
        op.create_index(
            op.f("ix_privacypreferencehistory_hashed_external_id"),
            "privacypreferencehistory",
            ["hashed_external_id"],
            unique=False,
        )
    else:
        logger.warning(
            "The privacypreferencehistory table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY ix_privacypreferencehistory_hashed_external_id "
            "ON privacypreferencehistory (hashed_external_id)'"
        )

    servednoticehistory_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM servednoticehistory")
    ).scalar()
    if servednoticehistory_count < 1000000:
        op.create_index(
            op.f("ix_servednoticehistory_hashed_external_id"),
            "servednoticehistory",
            ["hashed_external_id"],
            unique=False,
        )
    else:
        logger.warning(
            "The servednoticehistory table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY ix_servednoticehistory_hashed_external_id "
            "ON servednoticehistory (hashed_external_id)'"
        )


def downgrade():
    op.drop_index(
        op.f("ix_servednoticehistory_hashed_external_id"),
        table_name="servednoticehistory",
    )
    op.drop_column("servednoticehistory", "hashed_external_id")
    op.drop_column("servednoticehistory", "external_id")
    op.drop_index(
        op.f("ix_privacypreferencehistory_hashed_external_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "hashed_external_id")
    op.drop_column("privacypreferencehistory", "external_id")
    op.drop_constraint(
        "last_saved_for_phone_number_per_property_id",
        "currentprivacypreferencev2",
        type_="unique",
    )
    op.drop_constraint(
        "last_saved_for_fides_user_device_per_property_id",
        "currentprivacypreferencev2",
        type_="unique",
    )
    op.drop_constraint(
        "last_saved_for_external_id_per_property_id",
        "currentprivacypreferencev2",
        type_="unique",
    )
    op.drop_constraint(
        "last_saved_for_email_per_property_id",
        "currentprivacypreferencev2",
        type_="unique",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_property_id"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_external_id"),
        table_name="currentprivacypreferencev2",
    )
    op.create_unique_constraint(
        "last_saved_for_phone_number", "currentprivacypreferencev2", ["phone_number"]
    )
    op.create_unique_constraint(
        "last_saved_for_fides_user_device",
        "currentprivacypreferencev2",
        ["fides_user_device"],
    )
    op.create_unique_constraint(
        "last_saved_for_email", "currentprivacypreferencev2", ["email"]
    )
    op.drop_column("currentprivacypreferencev2", "property_id")
    op.drop_column("currentprivacypreferencev2", "hashed_external_id")
    op.drop_column("currentprivacypreferencev2", "external_id")
    op.drop_column("consentrequest", "property_id")
