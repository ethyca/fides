"""add is_hash_migrated column

Revision ID: 784f145ec892
Revises: eef4477c37d0
Create Date: 2024-09-03 21:04:21.880497

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "784f145ec892"
down_revision = "eef4477c37d0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "currentprivacypreferencev2",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.add_column(
        "custom_privacy_request_field",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.add_column(
        "providedidentity",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )

    connection = op.get_bind()

    # only run the index creation if the tables have less than 1 million rows
    currentprivacypreferencev2_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM currentprivacypreferencev2")
    ).scalar()
    if currentprivacypreferencev2_count < 1000000:
        op.create_index(
            "idx_currentprivacypreferencev2_unmigrated",
            "currentprivacypreferencev2",
            ["is_hash_migrated"],
            unique=False,
            postgresql_where=sa.text("is_hash_migrated IS false"),
        )
    else:
        logger.warning(
            "The currentprivacypreferencev2 table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY idx_currentprivacypreferencev2_unmigrated "
            "ON currentprivacypreferencev2 (is_hash_migrated) "
            "WHERE is_hash_migrated IS false'"
        )

    custom_privacy_request_field_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM custom_privacy_request_field")
    ).scalar()
    if custom_privacy_request_field_count < 1000000:
        op.create_index(
            "idx_custom_privacy_request_field_unmigrated",
            "custom_privacy_request_field",
            ["is_hash_migrated"],
            unique=False,
            postgresql_where=sa.text("is_hash_migrated IS false"),
        )
    else:
        logger.warning(
            "The custom_privacy_request_field table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY idx_custom_privacy_request_field_unmigrated "
            "ON custom_privacy_request_field (is_hash_migrated) "
            "WHERE is_hash_migrated IS false'"
        )

    privacypreferencehistory_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM privacypreferencehistory")
    ).scalar()
    if privacypreferencehistory_count < 1000000:
        op.create_index(
            "idx_privacypreferencehistory_unmigrated",
            "privacypreferencehistory",
            ["is_hash_migrated"],
            unique=False,
            postgresql_where=sa.text("is_hash_migrated IS false"),
        )
    else:
        logger.warning(
            "The privacypreferencehistory table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY idx_privacypreferencehistory_unmigrated "
            "ON privacypreferencehistory (is_hash_migrated) "
            "WHERE is_hash_migrated IS false'"
        )

    providedidentity_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM providedidentity")
    ).scalar()
    if providedidentity_count < 1000000:
        op.create_index(
            "idx_providedidentity_unmigrated",
            "providedidentity",
            ["is_hash_migrated"],
            unique=False,
            postgresql_where=sa.text("is_hash_migrated IS false"),
        )
    else:
        logger.warning(
            "The providedidentity table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY idx_providedidentity_unmigrated "
            "ON providedidentity (is_hash_migrated) "
            "WHERE is_hash_migrated IS false'"
        )

    servednoticehistory_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM servednoticehistory")
    ).scalar()
    if servednoticehistory_count < 1000000:
        op.create_index(
            "idx_servednoticehistory_unmigrated",
            "servednoticehistory",
            ["is_hash_migrated"],
            unique=False,
            postgresql_where=sa.text("is_hash_migrated IS false"),
        )
    else:
        logger.warning(
            "The servednoticehistory table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY idx_servednoticehistory_unmigrated "
            "ON servednoticehistory (is_hash_migrated) "
            "WHERE is_hash_migrated IS false'"
        )


def downgrade():
    op.drop_index(
        "idx_servednoticehistory_unmigrated",
        table_name="servednoticehistory",
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.drop_column("servednoticehistory", "is_hash_migrated")
    op.drop_index(
        "idx_providedidentity_unmigrated",
        table_name="providedidentity",
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.drop_column("providedidentity", "is_hash_migrated")
    op.drop_index(
        "idx_privacypreferencehistory_unmigrated",
        table_name="privacypreferencehistory",
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.drop_column("privacypreferencehistory", "is_hash_migrated")
    op.drop_index(
        "idx_custom_privacy_request_field_unmigrated",
        table_name="custom_privacy_request_field",
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.drop_column("custom_privacy_request_field", "is_hash_migrated")
    op.drop_index(
        "idx_currentprivacypreferencev2_unmigrated",
        table_name="currentprivacypreferencev2",
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.drop_column("currentprivacypreferencev2", "is_hash_migrated")
