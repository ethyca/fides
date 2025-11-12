"""add default identity definitions

Revision ID: b2c3d4e5f6a7
Revises: 7d82c8fc4c34
Create Date: 2024-11-11 18:27:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "7d82c8fc4c34"
branch_labels = None
depends_on = None

# Default identity keys to create
IDENTITY_KEYS = ["email", "phone_number", "fides_user_device_id", "external_id"]

# Privacy preferences partition tables
PARTITIONS = ["current", "historic"]


def upgrade():
    # Delete any existing entries for these identity keys
    # This handles cases where the API was already released and users may have created these
    op.execute(
        """
        DELETE FROM identity_definition
        WHERE identity_key IN ('email', 'phone_number', 'fides_user_device_id', 'external_id')
        """
    )

    # Insert default identity definitions
    op.execute(
        """
        INSERT INTO identity_definition (id, created_at, updated_at, identity_key, name, description, type, created_by)
        VALUES
          ('ide_' || gen_random_uuid(), now(), now(), 'email', 'Email', 'Email address', 'email', NULL),
          ('ide_' || gen_random_uuid(), now(), now(), 'phone_number', 'Phone number', 'Phone number', 'phone_number', NULL),
          ('ide_' || gen_random_uuid(), now(), now(), 'fides_user_device_id', 'Fides user device ID', 'Unique device identifier for Fides', 'uuid', NULL),
          ('ide_' || gen_random_uuid(), now(), now(), 'external_id', 'External ID', 'External identifier from another system', 'string', NULL)
        """
    )

    # Create indexes on privacy_preferences partitions for each identity key
    # These indexes enable efficient lookups on search_data->'identity'->>'{identity_key}'
    for identity_key in IDENTITY_KEYS:
        for partition in PARTITIONS:
            index_name = f"idx_identity_{identity_key}_{partition}"
            table_name = f"privacy_preferences_{partition}"
            op.execute(
                f"CREATE INDEX {index_name} "
                f"ON {table_name} ((search_data->'identity'->>{repr(identity_key)}))"
            )


def downgrade():
    # Drop indexes from privacy_preferences partitions
    for identity_key in IDENTITY_KEYS:
        for partition in PARTITIONS:
            index_name = f"idx_identity_{identity_key}_{partition}"
            op.execute(f"DROP INDEX IF EXISTS {index_name}")

    # Remove default identity definitions
    op.execute(
        """
        DELETE FROM identity_definition
        WHERE identity_key IN ('email', 'phone_number', 'fides_user_device_id', 'external_id')
        """
    )
