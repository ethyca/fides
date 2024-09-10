"""add is_hash_migrated column

Revision ID: 784f145ec892
Revises: eef4477c37d0
Create Date: 2024-09-03 21:04:21.880497

"""

import sqlalchemy as sa
from alembic import op

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
    op.create_index(
        "idx_currentprivacypreferencev2_unmigrated",
        "currentprivacypreferencev2",
        ["is_hash_migrated"],
        unique=False,
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.add_column(
        "custom_privacy_request_field",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.create_index(
        "idx_custom_privacy_request_field_unmigrated",
        "custom_privacy_request_field",
        ["is_hash_migrated"],
        unique=False,
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.create_index(
        "idx_privacypreferencehistory_unmigrated",
        "privacypreferencehistory",
        ["is_hash_migrated"],
        unique=False,
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.add_column(
        "providedidentity",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.create_index(
        "idx_providedidentity_unmigrated",
        "providedidentity",
        ["is_hash_migrated"],
        unique=False,
        postgresql_where=sa.text("is_hash_migrated IS false"),
    )
    op.add_column(
        "servednoticehistory",
        sa.Column("is_hash_migrated", sa.Boolean(), server_default="f", nullable=False),
    )
    op.create_index(
        "idx_servednoticehistory_unmigrated",
        "servednoticehistory",
        ["is_hash_migrated"],
        unique=False,
        postgresql_where=sa.text("is_hash_migrated IS false"),
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
