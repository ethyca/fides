"""add external id to privacy preference

Revision ID: d03cb217ac86
Revises: 4b2eade4353c
Create Date: 2024-05-28 17:29:07.303821

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "d03cb217ac86"
down_revision = "4b2eade4353c"
branch_labels = None
depends_on = None


def upgrade():
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
    op.create_unique_constraint(
        "last_saved_for_external_id", "currentprivacypreferencev2", ["external_id"]
    )
    op.add_column(
        "lastservednoticev2",
        sa.Column(
            "external_id",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "lastservednoticev2",
        sa.Column("hashed_external_id", sa.String(), nullable=True),
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
            "idx_preferences_gin",
            "currentprivacypreferencev2",
            [sa.text("(preferences -> 'preferences'::text) jsonb_path_ops")],
            unique=False,
            postgresql_using="gin",
        )
    else:
        logger.warning(
            "The currentprivacypreferencev2 table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run the following commands:\n"
            "- 'CREATE INDEX CONCURRENTLY ix_currentprivacypreferencev2_hashed_external_id "
            "ON currentprivacypreferencev2 (hashed_external_id)'\n"
            "- 'CREATE INDEX CONCURRENTLY idx_preferences_gin "
            "ON currentprivacypreferencev2 USING gin ((preferences->'preferences') jsonb_path_ops)'"
        )

    lastservednoticev2_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM lastservednoticev2")
    ).scalar()

    if lastservednoticev2_count < 1000000:
        op.create_index(
            op.f("ix_lastservednoticev2_hashed_external_id"),
            "lastservednoticev2",
            ["hashed_external_id"],
            unique=False,
        )
    else:
        logger.warning(
            "The lastservednoticev2 table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY ix_lastservednoticev2_hashed_external_id "
            "ON lastservednoticev2 (hashed_external_id)'"
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
    op.drop_index(
        op.f("ix_lastservednoticev2_hashed_external_id"),
        table_name="lastservednoticev2",
    )
    op.drop_column("lastservednoticev2", "hashed_external_id")
    op.drop_column("lastservednoticev2", "external_id")
    op.drop_constraint(
        "last_saved_for_external_id", "currentprivacypreferencev2", type_="unique"
    )
    op.drop_index(op.f("idx_preferences_gin"), table_name="currentprivacypreferencev2"),
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_external_id"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_column("currentprivacypreferencev2", "hashed_external_id")
    op.drop_column("currentprivacypreferencev2", "external_id")
