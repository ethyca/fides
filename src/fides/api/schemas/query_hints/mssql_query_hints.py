"""Microsoft SQL Server specific query hints."""

from enum import Enum
from typing import ClassVar, Optional, Set

from pydantic import model_validator

from fides.api.schemas.query_hints.base import QueryHint


class MSSQLHintType(str, Enum):
    """
    Supported Microsoft SQL Server query hints.

    Reference: https://learn.microsoft.com/en-us/sql/t-sql/queries/hints-transact-sql-query

    We explicitly enumerate only safe, performance-related hints.
    This prevents SQL injection by only allowing known hint types.
    """

    # Parallelism hints
    MAXDOP = "maxdop"

    # Future hints can be added here as needed:
    # RECOMPILE = "recompile"
    # OPTIMIZE_FOR_UNKNOWN = "optimize_for_unknown"
    # FAST = "fast"
    # MAXRECURSION = "maxrecursion"


class MSSQLQueryHint(QueryHint):
    """
    Microsoft SQL Server query hint.

    Example usage in Dataset YAML:
        fides_meta:
          query_hints:
            - hint_type: maxdop
              value: 1
    """

    connection_types: ClassVar[Set[str]] = {"mssql"}

    hint_type: MSSQLHintType
    value: Optional[int] = None

    @model_validator(mode="after")
    def validate_hint_value(self) -> "MSSQLQueryHint":
        """Validate that the hint has appropriate values."""
        if self.hint_type == MSSQLHintType.MAXDOP:
            if self.value is None:
                raise ValueError("MAXDOP hint requires a value")
            if not isinstance(self.value, int) or self.value < 0 or self.value > 64:
                raise ValueError("MAXDOP value must be an integer between 0 and 64")

        return self

    def to_sql_option(self) -> str:
        """Render as SQL OPTION clause component."""
        if self.hint_type == MSSQLHintType.MAXDOP:
            return f"MAXDOP {self.value}"

        # Future hints would be handled here
        raise ValueError(f"Unknown hint type: {self.hint_type}")
