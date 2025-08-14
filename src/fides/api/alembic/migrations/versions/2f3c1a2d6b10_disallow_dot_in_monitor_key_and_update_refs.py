"""disallow_dot_in_monitor_key_and_update_refs

Revision ID: 2f3c1a2d6b10
Revises: a7065df4dcf1
Create Date: 2025-08-11 00:00:00.000000

"""

from __future__ import annotations

import json
from typing import Dict

import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "2f3c1a2d6b10"
down_revision = "a7065df4dcf1"
branch_labels = None
depends_on = None


def _fetch_monitor_key_mapping(conn: Connection) -> Dict[str, str]:
    """
    Build a mapping of old monitor keys containing '.' to new, safe keys (replace '.' with '_').
    Ensures uniqueness by appending a short numeric suffix when needed.
    """
    rows = conn.execute(
        sa.text(
            """
        SELECT key FROM monitorconfig
    """
        )
    ).fetchall()
    existing_keys = {r[0] for r in rows}

    mapping: Dict[str, str] = {}
    taken: set[str] = set(existing_keys)

    for old_key in sorted(existing_keys):
        if "." not in old_key:
            continue
        base = old_key.replace(".", "_")
        new_key = base
        # ensure uniqueness
        if new_key in taken:
            i = 1
            while f"{base}_{i}" in taken:
                i += 1
            new_key = f"{base}_{i}"
        mapping[old_key] = new_key
        taken.add(new_key)

    if mapping:
        logger.info(
            f"Found {len(mapping)} monitor keys with dots, migrating monitorconfig keys based on mapping: {mapping}"
        )
    return mapping


def _update_monitorconfig_keys(conn: Connection, mapping: Dict[str, str]) -> None:
    logger.info("Updating monitorconfig keys...")
    for old, new in mapping.items():
        conn.execute(
            sa.text(
                """
                UPDATE monitorconfig
                SET key = :new
                WHERE key = :old
                """
            ),
            {"old": old, "new": new},
        )
    logger.info("Finished updating monitorconfig keys.")


def _update_monitorexecution(conn: Connection, mapping: Dict[str, str]) -> None:
    logger.info("Updating monitorexecution monitor_config_key...")
    for old, new in mapping.items():
        conn.execute(
            sa.text(
                """
                UPDATE monitorexecution
                SET monitor_config_key = :new
                WHERE monitor_config_key = :old
                """
            ),
            {"old": old, "new": new},
        )
    logger.info("Finished updating monitorexecution monitor_config_key.")


def _update_stagedresource_monitor_config_id(
    conn: Connection, mapping: Dict[str, str]
) -> None:
    logger.info("Updating stagedresource monitor_config_id...")
    for old, new in mapping.items():
        conn.execute(
            sa.text(
                """
                UPDATE stagedresource
                SET monitor_config_id = :new
                WHERE monitor_config_id = :old
                """
            ),
            {"old": old, "new": new},
        )
    logger.info("Finished updating stagedresource monitor_config_id.")


def _replace_prefix_sql(table: str, column: str) -> str:
    """
    Returns SQL snippet to replace leading '<old>.' prefix in a text column with '<new>.' while preserving the rest of the string.
    Assumes parameters :old and :new are bound.
    """
    # substring from old prefix length + 1 (since we want to keep the starting '.')
    return f"""
        UPDATE {table}
        SET {column} = :new || SUBSTRING({column} FROM CHAR_LENGTH(:old) + 1)
        WHERE {column} LIKE :old_prefix
    """


def _update_stagedresource_urns_and_parent(
    conn: Connection, mapping: Dict[str, str]
) -> None:
    logger.info("Updating stagedresource urns and parent...")
    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}
        # urn
        conn.execute(sa.text(_replace_prefix_sql("stagedresource", "urn")), params)
        # parent
        conn.execute(sa.text(_replace_prefix_sql("stagedresource", "parent")), params)
    logger.info("Finished updating stagedresource urns and parent.")


def _update_stagedresource_children_array(
    conn: Connection, mapping: Dict[str, str]
) -> None:
    logger.info("Updating stagedresource children array...")
    for old, new in mapping.items():
        conn.execute(
            sa.text(
                """
                UPDATE stagedresource
                SET children = (
                    SELECT COALESCE(array_agg(
                        CASE WHEN val LIKE :old_prefix
                             THEN :new || SUBSTRING(val FROM CHAR_LENGTH(:old) + 1)
                             ELSE val END
                    ), '{}')
                    FROM unnest(children) AS val
                )
                WHERE children IS NOT NULL
                AND EXISTS (SELECT 1 FROM unnest(children) AS v WHERE v LIKE :old_prefix)
                """
            ),
            {"old": old, "new": new, "old_prefix": f"{old}.%"},
        )
    logger.info("Finished updating stagedresource children array.")


def _update_stagedresource_meta_json(conn: Connection, mapping: Dict[str, str]) -> None:
    logger.info("Updating stagedresource meta json...")

    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}
        # Update direct_child_urns array in meta
        conn.execute(
            sa.text(
                """
                UPDATE stagedresource
                SET meta = jsonb_set(
                    COALESCE(meta, '{}'::jsonb),
                    '{direct_child_urns}',
                    (
                      SELECT COALESCE(jsonb_agg(
                        CASE WHEN elem LIKE :old_prefix
                             THEN to_jsonb(:new || SUBSTRING(elem FROM CHAR_LENGTH(:old) + 1))
                             ELSE to_jsonb(elem) END
                      ), '[]'::jsonb)
                      FROM jsonb_array_elements_text(COALESCE(meta->'direct_child_urns','[]'::jsonb)) AS elem
                    ),
                    true
                )
                WHERE meta ? 'direct_child_urns'
                """
            ),
            params,
        )
        # Update top_level_field_urn string in meta
        conn.execute(
            sa.text(
                """
                UPDATE stagedresource
                SET meta = jsonb_set(
                    COALESCE(meta, '{}'::jsonb),
                    '{top_level_field_urn}',
                    COALESCE(to_jsonb(
                        CASE WHEN (meta->>'top_level_field_urn') LIKE :old_prefix
                             THEN :new || SUBSTRING((meta->>'top_level_field_urn') FROM CHAR_LENGTH(:old) + 1)
                             ELSE (meta->>'top_level_field_urn') END
                    ), 'null'::jsonb),
                    true
                )
                WHERE meta ? 'top_level_field_urn'
                """
            ),
            params,
        )

    logger.info("Finished updating stagedresource meta json.")


def _update_stagedresourceancestor(conn: Connection, mapping: Dict[str, str]) -> None:
    logger.info("Updating stagedresourceancestor...")
    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}
        # ancestor_urn
        conn.execute(
            sa.text(_replace_prefix_sql("stagedresourceancestor", "ancestor_urn")),
            params,
        )
        # descendant_urn
        conn.execute(
            sa.text(_replace_prefix_sql("stagedresourceancestor", "descendant_urn")),
            params,
        )
    logger.info("Finished updating stagedresourceancestor.")


def upgrade() -> None:
    conn = op.get_bind()

    mapping = _fetch_monitor_key_mapping(conn)
    if mapping:
        logger.info("Beginning monitorconfig key 'dot' migration...")

        # Persist mapping into dbcache for API retrieval/debugging
        # NOTE: this mapping is persisted only as a temporary measure (i.e. for a few releases)
        # just in case we want to revert this data migration for any reason.
        # TODO: remove the cache entry in a future migration!
        logger.info("Persisting monitor key mapping to dbcache...")
        mapping_json = json.dumps(mapping)
        conn.execute(
            sa.text(
                """
                INSERT INTO dbcache (id, namespace, cache_key, cache_value, created_at, updated_at)
                VALUES ('dbc_' || gen_random_uuid(), :namespace, :cache_key, convert_to(:value, 'UTF8')::bytea, now(), now())
                ON CONFLICT (namespace, cache_key)
                DO UPDATE SET cache_value = EXCLUDED.cache_value, updated_at = now()
                """
            ),
            {
                "namespace": "monitor-config-key-mapping",
                "cache_key": "monitor-config-key-mapping",
                "value": mapping_json,
            },
        )
        logger.info("Finished persisting monitor key mapping to dbcache.")

        logger.info(
            "Dropping FKs to avoid immediate constraint violations while updating URNs..."
        )
        # Drop FKs to avoid immediate constraint violations while updating URNs
        op.drop_constraint(
            "fk_staged_resource_ancestor_ancestor",
            "stagedresourceancestor",
            type_="foreignkey",
        )
        op.drop_constraint(
            "fk_staged_resource_ancestor_descendant",
            "stagedresourceancestor",
            type_="foreignkey",
        )
        logger.info("Finished dropping FKs.")

        _update_monitorconfig_keys(conn, mapping)
        _update_monitorexecution(conn, mapping)
        _update_stagedresource_monitor_config_id(conn, mapping)
        _update_stagedresource_urns_and_parent(conn, mapping)
        _update_stagedresource_children_array(conn, mapping)
        _update_stagedresource_meta_json(conn, mapping)
        _update_stagedresourceancestor(conn, mapping)

        logger.info("Recreating FKs...")
        # Recreate FKs (mark DEFERRABLE to allow future migrations to defer checks during complex updates)
        op.create_foreign_key(
            "fk_staged_resource_ancestor_ancestor",
            "stagedresourceancestor",
            "stagedresource",
            ["ancestor_urn"],
            ["urn"],
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        )
        op.create_foreign_key(
            "fk_staged_resource_ancestor_descendant",
            "stagedresourceancestor",
            "stagedresource",
            ["descendant_urn"],
            ["urn"],
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        )
        logger.info("Finished recreating FKs.")

        logger.info("Finished monitorconfig key 'dot' migration.")

    # Add CHECK constraint to forbid dots in monitorconfig.key going forward
    op.create_check_constraint(
        "ck_monitorconfig_key_no_dots",
        "monitorconfig",
        "key NOT LIKE '%.%'",
    )


def downgrade() -> None:
    # Remove the CHECK constraint
    op.drop_constraint("ck_monitorconfig_key_no_dots", "monitorconfig", type_="check")
    # Data downgrade left blank intentionally - if needed, we have the old key mapping in
    # the dbcache entry and a data migration reversal can be written on an adhoc basis.
    pass
