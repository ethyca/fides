"""Query hints schemas for database-specific query optimization."""

from fides.api.schemas.query_hints.base import QueryHint, QueryHints
from fides.api.schemas.query_hints.mssql_query_hints import MSSQLHintType, MSSQLQueryHint

__all__ = [
    "QueryHint",
    "QueryHints",
    "MSSQLHintType",
    "MSSQLQueryHint",
]
