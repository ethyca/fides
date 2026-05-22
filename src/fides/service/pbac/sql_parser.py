"""Generic SQL parser — extracts table references from SQL text.

Uses sqlglot for dialect-agnostic SQL parsing.  Produces a
RawQueryLogEntry ready for the PBACEvaluationService.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

import sqlglot
import sqlglot.expressions as exp

from fides.service.pbac.types import RawQueryLogEntry, TableRef

logger = logging.getLogger(__name__)


def parse_query(
    query_text: str,
    user_identity: str,
    timestamp: datetime | None = None,
    source_id: str = "sql_parser",
) -> RawQueryLogEntry:
    """Parse generic SQL into a RawQueryLogEntry.

    Extracts table references and statement type using sqlglot
    (dialect-agnostic).  The resulting entry can be passed directly
    to ``PBACEvaluationService.evaluate()``.
    """
    tables = extract_table_refs(query_text)
    stmt_type = detect_statement_type(query_text)
    return RawQueryLogEntry(
        source_id=source_id,
        external_job_id=str(uuid4()),
        query_text=query_text,
        statement_type=stmt_type,
        referenced_tables=tables,
        timestamp=timestamp or datetime.now(timezone.utc),
        identity=user_identity,
    )


def extract_table_refs(query_text: str) -> list[TableRef]:
    """Extract table references from SQL using sqlglot."""
    refs: list[TableRef] = []
    try:
        parsed = sqlglot.parse(query_text)
    except Exception:
        logger.warning("Failed to parse SQL query for PBAC evaluation", exc_info=True)
        return refs

    for statement in parsed:
        if statement is None:
            continue
        for table in statement.find_all(exp.Table):
            # Skip subquery aliases and CTEs that show up as Table nodes
            if not table.name:
                continue
            refs.append(
                TableRef(
                    catalog=table.catalog or "",
                    schema=table.db or "",
                    table=table.name,
                )
            )
    return refs


def extract_columns(query_text: str) -> dict[str, list[str]]:
    """Extract column references per table from SQL using sqlglot.

    Returns ``{table_name: [column_name, ...]}``.
    Columns qualified with a table alias are resolved to the real
    table name.  Unqualified columns in single-table queries are
    attributed to that table.

    ``SELECT *`` and parse failures both return an empty dict,
    signalling that callers should fall back to all-columns behavior.
    """
    try:
        parsed = sqlglot.parse(query_text)
    except Exception:
        logger.warning("Failed to parse SQL for column extraction", exc_info=True)
        return {}

    alias_to_table: dict[str, str] = {}
    table_names: list[str] = []
    columns: dict[str, list[str]] = {}

    for statement in parsed:
        if statement is None:
            continue

        for table in statement.find_all(exp.Table):
            if not table.name:
                continue
            name = table.name.lower()
            alias = table.alias
            if alias:
                alias_to_table[alias.lower()] = name
            alias_to_table[name] = name
            if name not in table_names:
                table_names.append(name)

        for column in statement.find_all(exp.Column):
            col_name = column.name
            if not col_name:
                continue
            table_node = column.table
            if table_node:
                table_key = table_node.lower()
                resolved = alias_to_table.get(table_key, table_key)
            else:
                resolved = ""
            columns.setdefault(resolved, []).append(col_name)

    # Attribute unqualified columns to the table when only one exists
    if "" in columns and len(table_names) == 1:
        target = table_names[0]
        columns.setdefault(target, []).extend(columns.pop(""))

    return columns


def detect_statement_type(query_text: str) -> str:
    """Detect the SQL statement type from the query text."""
    # Strip leading single-line comments (-- ...) and block comments (/* ... */)
    normalized = query_text.strip()
    normalized = re.sub(r"^(--[^\n]*\n\s*)+", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"^(/\*.*?\*/\s*)+", "", normalized, flags=re.DOTALL)
    normalized = normalized.strip().upper()
    for stmt_type in (
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "MERGE",
        "CREATE",
        "DROP",
        "ALTER",
    ):
        if normalized.startswith(stmt_type):
            return stmt_type
    return "UNKNOWN"
