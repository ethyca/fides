"""disallow_dot_in_monitor_key_and_update_refs

Revision ID: 2f3c1a2d6b10
Revises: a7065df4dcf1
Create Date: 2025-08-11 00:00:00.000000

"""
from __future__ import annotations

from typing import Dict

from alembic import op
import sqlalchemy as sa
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
    rows = conn.execute(sa.text("""
        SELECT key FROM monitorconfig
    """)).fetchall()
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
    return mapping


def _update_monitorconfig_keys(conn: Connection, mapping: Dict[str, str]) -> None:
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


def _update_monitorexecution(conn: Connection, mapping: Dict[str, str]) -> None:
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


def _update_stagedresource_monitor_config_id(conn: Connection, mapping: Dict[str, str]) -> None:
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


def _replace_prefix_sql(prefix_col: str, table: str, column: str) -> str:
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


def _update_stagedresource_urns_and_parent(conn: Connection, mapping: Dict[str, str]) -> None:
    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}
        # urn
        conn.execute(sa.text(_replace_prefix_sql("urn", "stagedresource", "urn")), params)
        # parent
        conn.execute(sa.text(_replace_prefix_sql("parent", "stagedresource", "parent")), params)


def _update_stagedresource_children_array(conn: Connection, mapping: Dict[str, str]) -> None:
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


def _update_stagedresource_meta_json(conn: Connection, mapping: Dict[str, str]) -> None:
    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}
        # Update direct_child_urns array in meta
        conn.execute(
            sa.text(
                """
                UPDATE stagedresource
                SET meta = jsonb_set(
                    meta,
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
                    meta,
                    '{top_level_field_urn}',
                    to_jsonb(
                        CASE WHEN (meta->>'top_level_field_urn') LIKE :old_prefix
                             THEN :new || SUBSTRING((meta->>'top_level_field_urn') FROM CHAR_LENGTH(:old) + 1)
                             ELSE (meta->>'top_level_field_urn') END
                    ),
                    true
                )
                WHERE meta ? 'top_level_field_urn'
                """
            ),
            params,
        )


def _update_stagedresourceancestor(conn: Connection, mapping: Dict[str, str]) -> None:
    for old, new in mapping.items():
        params = {"old": old, "new": new, "old_prefix": f"{old}.%"}
        # ancestor_urn
        conn.execute(sa.text(_replace_prefix_sql("ancestor_urn", "stagedresourceancestor", "ancestor_urn")), params)
        # descendant_urn
        conn.execute(sa.text(_replace_prefix_sql("descendant_urn", "stagedresourceancestor", "descendant_urn")), params)


def upgrade() -> None:
    conn = op.get_bind()

    mapping = _fetch_monitor_key_mapping(conn)
    if mapping:
        _update_monitorconfig_keys(conn, mapping)
        _update_monitorexecution(conn, mapping)
        _update_stagedresource_monitor_config_id(conn, mapping)
        _update_stagedresource_urns_and_parent(conn, mapping)
        _update_stagedresource_children_array(conn, mapping)
        _update_stagedresource_meta_json(conn, mapping)
        _update_stagedresourceancestor(conn, mapping)

    # Add CHECK constraint to forbid dots in monitorconfig.key going forward
    op.create_check_constraint(
        "ck_monitorconfig_key_no_dots",
        "monitorconfig",
        "key NOT LIKE '%.%'",
    )


def downgrade() -> None:
    # Remove the CHECK constraint
    op.drop_constraint("ck_monitorconfig_key_no_dots", "monitorconfig", type_="check")
    # Data downgrades are not supported because the original keys are not retained.
    # This is intentional to keep references consistent.
    pass