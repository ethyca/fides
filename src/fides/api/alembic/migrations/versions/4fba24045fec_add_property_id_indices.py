"""add property_id indices

Revision ID: 4fba24045fec
Revises: 57479150efd6
Create Date: 2024-05-17 19:25:36.539636

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "4fba24045fec"
down_revision = "57479150efd6"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # only run the index creation if the tables have less than 1 million rows
    privacypreferencehistory_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM privacypreferencehistory")
    ).scalar()
    if privacypreferencehistory_count < 1000000:
        op.create_index(
            op.f("ix_privacypreferencehistory_property_id"),
            "privacypreferencehistory",
            ["property_id"],
            unique=False,
        )
    else:
        logger.warning(
            "The privacypreferencehistory table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY ix_privacypreferencehistory_property_id "
            "ON privacypreferencehistory (property_id)'"
        )

    servednoticehistory_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM servednoticehistory")
    ).scalar()
    if servednoticehistory_count < 1000000:
        op.create_index(
            op.f("ix_servednoticehistory_property_id"),
            "servednoticehistory",
            ["property_id"],
            unique=False,
        )
    else:
        logger.warning(
            "The servednoticehistory table has more than 1 million rows, "
            "skipping index creation. Be sure to manually run "
            "'CREATE INDEX CONCURRENTLY ix_servednoticehistory_property_id "
            "ON servednoticehistory (property_id)'"
        )


def downgrade():
    op.drop_index(
        op.f("ix_servednoticehistory_property_id"), table_name="servednoticehistory"
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_property_id"),
        table_name="privacypreferencehistory",
    )
