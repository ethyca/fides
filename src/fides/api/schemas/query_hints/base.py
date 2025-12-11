"""Base classes for query hints."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Set, Type

from loguru import logger
from pydantic import BaseModel


class QueryHint(BaseModel, ABC):
    """
    Base class for database-specific query hints.

    Each database implementation must define:
    - The hint type enum
    - Validation for hint values
    - How to render the hint as SQL
    """

    # Registry of implementations by connection type
    _implementations: ClassVar[Dict[str, Type["QueryHint"]]] = {}

    # The connection types this hint applies to
    connection_types: ClassVar[Set[str]] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for conn_type in cls.connection_types:
            cls._implementations[conn_type] = cls

    @classmethod
    def get_implementation(cls, connection_type: str) -> Optional[Type["QueryHint"]]:
        """Get the QueryHint implementation for a connection type."""
        return cls._implementations.get(connection_type)

    @classmethod
    def get_supported_connection_types(cls) -> Set[str]:
        """Get all connection types that support query hints."""
        return set(cls._implementations.keys())

    @abstractmethod
    def to_sql_option(self) -> str:
        """
        Render this hint as a SQL OPTION clause component.

        Returns the hint without the OPTION() wrapper, e.g., "MAXDOP 1"
        """


class QueryHints(BaseModel):
    """
    Container for multiple query hints that can be specified on a Collection.

    Example YAML:
        fides_meta:
          query_hints:
            - hint_type: maxdop
              value: 1
    """

    hints: List[Dict[str, Any]] = []

    def get_hints_for_connection_type(self, connection_type: str) -> List[QueryHint]:
        """
        Parse and validate hints for a specific connection type.
        Returns only hints that are valid for this connection type.
        """
        implementation = QueryHint.get_implementation(connection_type)
        if implementation is None:
            return []

        valid_hints = []
        for hint_dict in self.hints:
            try:
                hint = implementation.model_validate(hint_dict)
                valid_hints.append(hint)
            except (ValueError, Exception) as exc:
                # Skip hints that don't validate for this connection type
                logger.debug(
                    "Skipping invalid query hint for connection type {}: {}",
                    connection_type,
                    exc,
                )
                continue

        return valid_hints

    def to_sql_option_clause(self, connection_type: str) -> Optional[str]:
        """
        Generate the full SQL OPTION clause for this connection type.

        Returns None if no valid hints exist for this connection type.
        Returns e.g., "OPTION (MAXDOP 1)" for MSSQL.
        """
        hints = self.get_hints_for_connection_type(connection_type)
        if not hints:
            return None

        hint_parts = [hint.to_sql_option() for hint in hints]
        return f"OPTION ({', '.join(hint_parts)})"
