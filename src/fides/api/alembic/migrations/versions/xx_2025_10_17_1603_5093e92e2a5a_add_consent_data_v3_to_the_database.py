"""Add consent data v3 to the database

Revision ID: 5093e92e2a5a
Revises: a55e12c2c2df
Create Date: 2025-10-17 16:03:37.933367

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import BigInteger, Identity
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5093e92e2a5a"
down_revision = "a55e12c2c2df"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "privacy_preferences",
        # Use a big integer for the primary key to ensure we have enough space for all the records
        # and also force the ID to be generated, never allowing it to be overridden without expressly using `OVERRIDING SYSTEM VALUE`
        sa.Column(
            "id",
            BigInteger,
            Identity(start=1, increment=1, always=True),
            primary_key=True,
        ),
        sa.Column("search_data", postgresql.JSONB),
        sa.Column("record_data", postgresql.TEXT),
        # If we have a primary key we need to use a composite key because the primary key must be unique across _all_
        # partitions, so we can't just use `id`, we have to use `is_latest` as well as part of the primary key. This
        # should not be problematic as we will not allow for manually providing the ID so (unless someone deliberately does it)
        # we should not end up with duplicate IDs having different `is_latest` values.
        sa.Column(
            "is_latest",
            postgresql.BOOLEAN,
            nullable=False,
            server_default="f",
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        postgresql_partition_by="LIST (is_latest)",
    )
    # Create our partition tables using _current and _historic as suffixes
    op.execute(
        """
            CREATE TABLE privacy_preferences_current
            PARTITION OF privacy_preferences
            FOR VALUES IN (true);
            """
    )
    op.execute(
        """
            CREATE TABLE privacy_preferences_historic
            PARTITION OF privacy_preferences
            FOR VALUES IN (false);
            """
    )


def downgrade():
    op.drop_table("privacy_preferences")
