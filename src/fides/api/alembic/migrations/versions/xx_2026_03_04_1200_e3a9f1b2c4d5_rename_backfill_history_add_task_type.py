"""Rename backfill_history to post_upgrade_background_migration_tasks, add task_type column

Revision ID: e3a9f1b2c4d5
Revises: 074796d61d8a
Create Date: 2026-03-04 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e3a9f1b2c4d5"
down_revision = "074796d61d8a"
branch_labels = None
depends_on = None

# All existing TABLE_OBJECT_MAP index/constraint names that predate this migration.
# Since these migrations cannot be modified retroactively, we pre-register them here
# so the background script knows they are safe to process.
EXISTING_INDEX_KEYS = [
    "ix_currentprivacypreferencev2_email_property_id",
    "ix_currentprivacypreferencev2_external_id_property_id",
    "ix_currentprivacypreferencev2_fides_user_device_property_id",
    "ix_currentprivacypreferencev2_phone_number_property_id",
    "ix_currentprivacypreferencev2_hashed_external_id",
    "last_saved_for_email_per_property_id",
    "last_saved_for_external_id_per_property_id",
    "last_saved_for_fides_user_device_per_property_id",
    "last_saved_for_phone_number_per_property_id",
    "ix_privacypreferencehistory_hashed_external_id",
    "ix_providedidentity_privacy_request_id",
    "ix_providedidentity_reqid_field_hash",
    "ix_privacyrequest_policy_created",
    "ix_servednoticehistory_hashed_external_id",
    "ix_staged_resource_ancestor_pkey",
    "ix_staged_resource_ancestor_unique",
    "uq_staged_resource_ancestor",
    "fk_staged_resource_ancestor_ancestor",
    "fk_staged_resource_ancestor_descendant",
    "ix_staged_resource_ancestor_ancestor",
    "ix_staged_resource_ancestor_descendant",
    "ix_staged_resource_ancestor_desc_anc_dist",
    "ix_staged_resource_ancestor_anc_dist_desc",
    "ix_stagedresource_monitor_config_resource_type_consent",
    "ix_stagedresource_system_vendor_consent",
    "idx_stagedresource_user_categories_gin",
    "idx_stagedresource_classifications_gin",
    "ix_stagedresource_monitor_leaf_status_urn",
    "ix_stagedresource_leaf_true_monitor_status_urn",
]


def upgrade() -> None:
    op.rename_table("backfill_history", "post_upgrade_background_migration_tasks")
    op.alter_column(
        "post_upgrade_background_migration_tasks",
        "backfill_name",
        new_column_name="key",
        existing_type=sa.String(255),
        existing_nullable=False,
    )
    # Add with server_default so existing rows (backfill records) get populated
    op.add_column(
        "post_upgrade_background_migration_tasks",
        sa.Column(
            "task_type",
            sa.String(50),
            nullable=False,
            server_default="backfill",
        ),
    )
    # Drop the server default — callers must supply task_type explicitly going forward
    op.alter_column(
        "post_upgrade_background_migration_tasks",
        "task_type",
        existing_type=sa.String(50),
        existing_nullable=False,
        server_default=None,
    )

    # Replace the inherited single-column PK on `key` with a surrogate `id` PK
    # and a composite unique constraint on (task_type, key).
    # This allows different task_types to share the same key name.
    op.drop_constraint(
        "backfill_history_pkey",
        "post_upgrade_background_migration_tasks",
        type_="primary",
    )
    op.add_column(
        "post_upgrade_background_migration_tasks",
        sa.Column(
            "id",
            sa.String(36),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.create_primary_key(
        "post_upgrade_background_migration_tasks_pkey",
        "post_upgrade_background_migration_tasks",
        ["id"],
    )
    # Composite unique constraint replaces both the old PK uniqueness on `key`
    # and any standalone task_type index
    op.create_unique_constraint(
        "uq_post_upgrade_background_migration_tasks_task_type_key",
        "post_upgrade_background_migration_tasks",
        ["task_type", "key"],
    )

    # Make completed_at nullable: NULL means "registered/in-progress", non-NULL means "done"
    op.alter_column(
        "post_upgrade_background_migration_tasks",
        "completed_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
    )

    # Pre-register all existing deferred index entries whose migrations predate this change.
    # These indexes predate the new completed_at semantics, so we explicitly set
    # completed_at = now() to preserve current behavior.
    values_clause = ", ".join(
        f"('{key}', 'index', now())" for key in EXISTING_INDEX_KEYS
    )
    op.execute(
        f"INSERT INTO post_upgrade_background_migration_tasks (key, task_type, completed_at) "
        f"VALUES {values_clause} ON CONFLICT (task_type, key) DO NOTHING"
    )


def downgrade() -> None:
    # Restore completed_at: backfill NULLs, re-add server_default, set NOT NULL
    op.execute(
        "UPDATE post_upgrade_background_migration_tasks "
        "SET completed_at = now() WHERE completed_at IS NULL"
    )
    op.alter_column(
        "post_upgrade_background_migration_tasks",
        "completed_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )

    # Delete the rows for type index
    op.execute(
        "DELETE FROM post_upgrade_background_migration_tasks WHERE task_type = 'index'"
    )

    # Reverse the surrogate PK change: drop composite unique index, PK, and id column,
    # then restore PK on key
    op.drop_constraint(
        "uq_post_upgrade_background_migration_tasks_task_type_key",
        "post_upgrade_background_migration_tasks",
        type_="unique",
    )
    op.drop_constraint(
        "post_upgrade_background_migration_tasks_pkey",
        "post_upgrade_background_migration_tasks",
        type_="primary",
    )
    op.drop_column("post_upgrade_background_migration_tasks", "id")
    op.create_primary_key(
        "backfill_history_pkey",
        "post_upgrade_background_migration_tasks",
        ["key"],
    )

    # Remove task_type and change key back to name
    op.drop_column("post_upgrade_background_migration_tasks", "task_type")
    op.alter_column(
        "post_upgrade_background_migration_tasks",
        "key",
        new_column_name="backfill_name",
        existing_type=sa.String(255),
        existing_nullable=False,
    )
    # Rename table back to backfill_history
    op.rename_table("post_upgrade_background_migration_tasks", "backfill_history")
