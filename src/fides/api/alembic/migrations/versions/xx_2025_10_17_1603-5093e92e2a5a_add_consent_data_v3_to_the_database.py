"""Add consent data v3 to the database

Revision ID: 5093e92e2a5a
Revises: a55e12c2c2df
Create Date: 2025-10-17 16:03:37.933367

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5093e92e2a5a"
down_revision = "a55e12c2c2df"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "consent_documents",
        sa.Column("search_data", postgresql.json.JSONB),
        sa.Column("record_data", postgresql.TEXT),
        sa.Column("is_latest", postgresql.BOOLEAN, nullable=False, server_default="f"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("consented_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        postgresql_partition_by="LIST (is_latest)",
    )
    # Create our partition tables using _current and _historic as suffixes
    op.execute(
        """
            CREATE TABLE consent_documents_current
            PARTITION OF consent_documents
            FOR VALUES IN (true);
            """
    )
    op.execute(
        """
            CREATE TABLE consent_documents_historic
            PARTITION OF consent_documents
            FOR VALUES IN (false);
            """
    )


def downgrade():
    op.drop_table("consent_documents")
    pass
