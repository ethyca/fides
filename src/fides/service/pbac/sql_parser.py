"""Generic SQL parser — extracts table references from SQL text.

Uses sqlglot for dialect-agnostic SQL parsing.  Produces a
RawQueryLogEntry ready for the PBACEvaluationService.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import sqlglot  # type: ignore[import-not-found]
import sqlglot.expressions as exp  # type: ignore[import-not-found]

from fides.service.pbac.types import RawQueryLogEntry, TableRef


def parse_query(
    query_text: str,
    user_email: str,
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
        user_email=user_email,
        query_text=query_text,
        statement_type=stmt_type,
        referenced_tables=tables,
        timestamp=timestamp or datetime.now(timezone.utc),
    )


def extract_table_refs(query_text: str) -> list[TableRef]:
    """Extract table references from SQL using sqlglot."""
    refs: list[TableRef] = []
    try:
        parsed = sqlglot.parse(query_text)
    except Exception:
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
                    project=table.catalog or "",
                    dataset=table.db or "",
                    table=table.name,
                )
            )
    return refs


def detect_statement_type(query_text: str) -> str:
    """Detect the SQL statement type from the query text."""
    import re

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
