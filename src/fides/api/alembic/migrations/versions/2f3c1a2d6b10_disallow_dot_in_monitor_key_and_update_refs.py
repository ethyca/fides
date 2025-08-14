"""
Disallow dots in monitor keys and update references to monitor keys.

This is a data migration.

This migration does the following:
- Fetches a mapping of old monitor keys containing '.' to new, safe keys (replace '.' with '_').
- Persists the mapping into the dbcache table.
- Drops the FK constraints on the stagedresourceancestor table.
- Updates the monitorconfig.key, monitorexecution.monitor_config_key, stagedresource.monitor_config_id, stagedresource.urn, stagedresource.parent, stagedresource.children, stagedresource.meta, stagedresourceancestor.ancestor_urn, and stagedresourceancestor.descendant_urn to reference new keys.
- Recreates the FK constraints on the stagedresourceancestor table.
- Adds a CHECK constraint to forbid dots in monitorconfig.key going forward.

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
    """
    Updates `MonitorConfig.key`s based on the mapping of 'old' keys to 'new' keys.
    """

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
    """
    Updates `monitorexecution.monitor_config_key` to reference new `MonitorConfig.key`s.
    """

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
    """
    Updates `stagedresource.monitor_config_id` to reference new `MonitorConfig.key`s.
    """
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


def _update_stagedresource_urns_and_parent(
    conn: Connection, mapping: Dict[str, str]
) -> None:
    """
    Updates `stagedresource.urn`s and `stagedresource.parent`s to reference new `MonitorConfig.key`s.
    """
    logger.info("Updating stagedresource urns and parent...")
    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}

        conn.execute(
            sa.text(
                f"""
                UPDATE stagedresource
                SET urn = :new || SUBSTRING(urn FROM CHAR_LENGTH(:old) + 1)
                WHERE urn LIKE :old_prefix AND monitor_config_id = :new
                """
            ),
            params,
        )

        conn.execute(
            sa.text(
                f"""
                UPDATE stagedresource
                SET parent = :new || SUBSTRING(parent FROM CHAR_LENGTH(:old) + 1)
                WHERE parent LIKE :old_prefix AND monitor_config_id = :new
                """
            ),
            params,
        )
    logger.info("Finished updating stagedresource urns and parent.")


def _update_stagedresource_children_array(
    conn: Connection, mapping: Dict[str, str]
) -> None:
    """
    Updates `stagedresource.children` to reference new `MonitorConfig.key`s.

    Elements from `stagedresource.children` are unnested, updated, and re-aggregated in a single query.
    """
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
                WHERE monitor_config_id = :new
                AND children IS NOT NULL
                """
            ),
            {"old": old, "new": new, "old_prefix": f"{old}.%"},
        )
    logger.info("Finished updating stagedresource children array.")


def _update_stagedresource_meta_json(conn: Connection, mapping: Dict[str, str]) -> None:
    """
    Updates necessary keys in `stagedresource.meta` (`direct_child_urns` and `top_level_field_urn`)
    to reference new `MonitorConfig.key`s.
    """
    logger.info("Updating stagedresource meta json...")

    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}

        # updates `stagedresource.meta.direct_child_urns` to reference new `MonitorConfig.key`
        # elements from `stagedresource.meta.direct_child_urns` are unnested, updated, and re-aggregated in a single query.
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
                WHERE monitor_config_id = :new AND meta ? 'direct_child_urns'
                """
            ),
            params,
        )

        # updates `stagedresource.meta.top_level_field_urn` to reference new `MonitorConfig.key`
        # we coalesce the value to 'null'::jsonb to ensure a 'JSON null' value is set, not a column-level NULL
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
                WHERE monitor_config_id = :new AND meta ? 'top_level_field_urn'
                """
            ),
            params,
        )

    logger.info("Finished updating stagedresource meta json.")


def _update_stagedresourceancestor(conn: Connection, mapping: Dict[str, str]) -> None:
    """
    Updates `stagedresourceancestor.ancestor_urn` and `stagedresourceancestor.descendant_urn`
    to reference new `MonitorConfig.key`s.

    NOTE: StagedResourceAncestor queries cannot be easily scoped by monitor_config_id
    since the table doesn't have a direct reference to it. However, we optimize by
    doing a single table scan to update both columns for all mappings at once.

    The generated query will look like:
    ```
    UPDATE stagedresourceancestor
    SET
        ancestor_urn = CASE
            WHEN ancestor_urn LIKE 'monitor.config.1.%' THEN 'monitor_config_1' || SUBSTRING(ancestor_urn FROM 17)
            WHEN ancestor_urn LIKE 'monitor.config.2.%' THEN 'monitor_config_2' || SUBSTRING(ancestor_urn FROM 17)
            ELSE ancestor_urn
        END,
        descendant_urn = CASE
            WHEN descendant_urn LIKE 'monitor.config.1.%' THEN 'monitor_config_1' || SUBSTRING(descendant_urn FROM 17)
            WHEN descendant_urn LIKE 'monitor.config.2.%' THEN 'monitor_config_2' || SUBSTRING(descendant_urn FROM 17)
            ELSE descendant_urn
        END
    WHERE ancestor_urn LIKE 'monitor.config.1.%' OR descendant_urn LIKE 'monitor.config.1.%'
       OR ancestor_urn LIKE 'monitor.config.2.%' OR descendant_urn LIKE 'monitor.config.2.%'
    ```
    """
    logger.info("Updating stagedresourceancestor...")

    if not mapping:
        return

    ancestor_case_conditions = []
    descendant_case_conditions = []
    where_conditions = []

    for old, new in mapping.items():
        ancestor_case_conditions.append(
            f"WHEN ancestor_urn LIKE '{old}.%' THEN '{new}' || SUBSTRING(ancestor_urn FROM {len(old) + 1})"
        )
        descendant_case_conditions.append(
            f"WHEN descendant_urn LIKE '{old}.%' THEN '{new}' || SUBSTRING(descendant_urn FROM {len(old) + 1})"
        )
        where_conditions.extend(
            [f"ancestor_urn LIKE '{old}.%'", f"descendant_urn LIKE '{old}.%'"]
        )

    sql = f"""
        UPDATE stagedresourceancestor
        SET
            ancestor_urn = CASE
                {' '.join(ancestor_case_conditions)}
                ELSE ancestor_urn
            END,
            descendant_urn = CASE
                {' '.join(descendant_case_conditions)}
                ELSE descendant_urn
            END
        WHERE {' OR '.join(where_conditions)}
    """

    conn.execute(sa.text(sql))
    logger.info("Finished updating stagedresourceancestor.")


def _persist_monitor_key_mapping(conn: Connection, mapping: Dict[str, str]) -> None:
    """
    Persists the mapping of 'old' monitor keys with dots in them to 'new' keys without dots
    into the dbcache table.

    NOTE: this mapping is persisted only as a temporary measure (i.e. for a few releases)
    just in case we want to revert this data migration for any reason.


    TODO: remove the cache entry in a future migration!
    """
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


def _drop_fk_constraints(conn: Connection) -> None:
    """
    Drops the FK constraints on the stagedresourceancestor table.

    This is done to avoid immediate constraint violations while updating URNs.
    """
    logger.info("Dropping FK constraints...")
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
    logger.info("Finished dropping FK constraints.")


def _recreate_fk_constraints(conn: Connection) -> None:
    """
    Recreates the FK constraints on the stagedresourceancestor table.
    """
    logger.info("Recreating FK constraints...")
    op.create_foreign_key(
        "fk_staged_resource_ancestor_ancestor",
        "stagedresourceancestor",
        "stagedresource",
        ["ancestor_urn"],
        ["urn"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_staged_resource_ancestor_descendant",
        "stagedresourceancestor",
        "stagedresource",
        ["descendant_urn"],
        ["urn"],
        ondelete="CASCADE",
    )
    logger.info("Finished recreating FK constraints.")


def upgrade() -> None:
    conn = op.get_bind()

    mapping = _fetch_monitor_key_mapping(conn)
    if mapping:
        logger.info("Beginning monitorconfig key 'dot' migration...")
        logger.info(
            f"Found {len(mapping)} monitor configs with dots to migrate: {list(mapping.keys())}"
        )

        _persist_monitor_key_mapping(conn, mapping)

        _drop_fk_constraints(conn)

        _update_monitorconfig_keys(conn, mapping)
        _update_monitorexecution(conn, mapping)
        _update_stagedresource_monitor_config_id(conn, mapping)
        _update_stagedresource_urns_and_parent(conn, mapping)
        _update_stagedresource_children_array(conn, mapping)
        _update_stagedresource_meta_json(conn, mapping)
        _update_stagedresourceancestor(conn, mapping)

        _recreate_fk_constraints(conn)

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
