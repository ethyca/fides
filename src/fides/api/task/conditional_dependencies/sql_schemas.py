import types
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, any_, bindparam

from fides.api.task.conditional_dependencies.schemas import Operator


class SQLTranslationError(Exception):
    """Error raised when SQL translation fails"""


def _escape_like_pattern(val: Any) -> str:
    """
    Escape LIKE wildcards in user input to prevent pattern injection attacks.

    This prevents users from injecting wildcards (% and _) that could:
    - Match unintended records through pattern injection
    - Cause performance issues with expensive wildcard operations
    - Enable information disclosure through pattern probing

    Note: This function escapes ALL % and _ characters as a security measure.
    While this may seem aggressive for normal field names, it's necessary because:
    1. We can't distinguish between intentional and malicious wildcards
    2. Field values shouldn't typically contain SQL wildcards
    3. Better to be overly cautious with user input

    Args:
        val: User input value to escape

    Returns:
        Escaped string safe for use in LIKE patterns

    Examples:
        _escape_like_pattern("admin%") -> "admin\\%"
        _escape_like_pattern("test_user") -> "test\\_user"  # Escapes _ for security
        _escape_like_pattern("normal") -> "normal"
    """
    if val is None:
        return ""

    val_str = str(val)
    # Escape backslashes first to prevent double-escaping
    # Then escape LIKE wildcards (% and _)
    return val_str.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _validate_and_escape_json_path_component(component: str) -> str:
    """
    Validate and escape JSON path components to prevent injection attacks.

    This prevents users from injecting malicious content in JSON path components that could:
    - Break out of single quotes in PostgreSQL JSON operators
    - Inject arbitrary SQL through malformed JSON paths
    - Cause syntax errors or unexpected behavior

    Args:
        component: JSON path component to validate and escape

    Returns:
        Validated and escaped component safe for use in PostgreSQL JSON operators

    Raises:
        SQLTranslationError: If the component contains invalid characters

    Examples:
        _validate_and_escape_json_path_component("field") -> "field"
        _validate_and_escape_json_path_component("field'name") -> "field''name"
        _validate_and_escape_json_path_component("") -> raises SQLTranslationError
    """
    if not component or not isinstance(component, str):
        raise SQLTranslationError(
            f"Invalid JSON path component: '{component}'. Components must be non-empty strings."
        )

    # Check for potentially dangerous characters
    if len(component) > 100:  # Reasonable limit for JSON field names
        raise SQLTranslationError(
            f"JSON path component too long: '{component[:50]}...'. Maximum length is 100 characters."
        )

    # Escape single quotes for PostgreSQL JSON operators (double them)
    escaped_component = component.replace("'", "''")

    return escaped_component


def _handle_list_contains(col: Column, val: Any) -> Column:
    """
    Handle list_contains operator for different scenarios:
    - If val is a list: check if column value is IN the list
    - If val is a single value: check if column contains the value (for arrays/JSON) or use LIKE (for strings)

    Args:
        col: SQLAlchemy column
        val: Value to compare against

    Returns:
        SQLAlchemy expression for the comparison
    """
    if isinstance(val, list):
        # If value is a list, check if column value is IN the list
        return col.in_(val)

    # For single values, we need to handle different column types
    # Check if this is a PostgreSQL array column
    if hasattr(col.type, "item_type") or str(col.type).startswith("ARRAY"):
        # This is a PostgreSQL array - use the ANY operator with proper parameter binding
        # This is safer and prevents SQL injection
        # Generate unique parameter name to avoid conflicts when multiple list operations exist in same query
        unique_param_name = f"array_val_{uuid.uuid4().hex[:8]}"
        param = bindparam(unique_param_name, val)
        return param == any_(col)

    # Try JSON containment for JSONB/JSON columns
    try:
        return col.contains(val)
    except Exception:
        # Fallback to LIKE for string columns with escaped wildcards
        escaped_val = _escape_like_pattern(val)
        return col.like(f"%{escaped_val}%", escape="\\")


OPERATOR_MAP = types.MappingProxyType(
    {
        Operator.eq: lambda col, val: col == val,
        Operator.neq: lambda col, val: col != val,
        Operator.lt: lambda col, val: col < val,
        Operator.lte: lambda col, val: col <= val,
        Operator.gt: lambda col, val: col > val,
        Operator.gte: lambda col, val: col >= val,
        Operator.contains: lambda col, val: col.like(
            f"%{_escape_like_pattern(val)}%", escape="\\"
        ),
        Operator.starts_with: lambda col, val: col.like(
            f"{_escape_like_pattern(val)}%", escape="\\"
        ),
        Operator.ends_with: lambda col, val: col.like(
            f"%{_escape_like_pattern(val)}", escape="\\"
        ),
        Operator.exists: lambda col, val: col.isnot(None),
        Operator.not_exists: lambda col, val: col.is_(None),
        Operator.list_contains: _handle_list_contains,
        Operator.not_in_list: lambda col, val: ~_handle_list_contains(col, val),
    }
)


class FieldAddress(BaseModel):
    """Parsed field address with table and column information"""

    table_name: str = Field(description="Table name extracted from field address")
    column_name: str = Field(description="Base column name without JSON path")
    json_path: Optional[list[str]] = Field(
        default=None, description="JSON path components if this is a JSON field"
    )
    full_address: str = Field(description="Original field address string")

    def __hash__(self) -> int:
        """Make FieldAddress hashable for use in sets"""
        return hash(
            (
                self.table_name,
                self.column_name,
                tuple(self.json_path) if self.json_path else None,
            )
        )

    def __eq__(self, other: Any) -> bool:
        """Enable equality comparison for FieldAddress objects"""
        if not isinstance(other, FieldAddress):
            return False
        return (
            self.table_name == other.table_name
            and self.column_name == other.column_name
            and self.json_path == other.json_path
        )

    def to_sql_column(self, enable_json_operators: bool = True) -> str:
        """
        Convert field address to PostgreSQL column reference

        Args:
            enable_json_operators: Whether to use PostgreSQL JSON operators for JSON paths

        Returns:
            SQL column reference string
        """
        is_json_path = self.json_path is not None and len(self.json_path) > 0
        if not is_json_path or not enable_json_operators:
            return self.column_name

        if self.json_path is None:
            # This should never happen
            raise SQLTranslationError(
                "Field address internal error."
            )  # pragma: no cover

        # Build PostgreSQL JSON path: column->'path'->'path'->>'final_path'
        # Validate and escape all components to prevent injection
        if self.json_path and len(self.json_path) == 1:
            # Simple case: column->>'field'
            escaped_component = _validate_and_escape_json_path_component(
                self.json_path[0]
            )
            return f"{self.column_name}->>'{escaped_component}'"

        # Complex case: column->'field'->'field'->>'final_field'
        path_parts = []
        # All but last use -> operator
        for part in self.json_path[:-1]:
            escaped_part = _validate_and_escape_json_path_component(part)
            path_parts.append(f"->'{escaped_part}'")
        # Last part uses ->> operator (returns text)
        escaped_final = _validate_and_escape_json_path_component(self.json_path[-1])
        path_parts.append(f"->>'{escaped_final}'")

        return f"{self.column_name}{''.join(path_parts)}"

    @classmethod
    def _parse_parts_to_components(
        cls, parts: list[str]
    ) -> tuple[str, str, Optional[list[str]]]:
        """
        Parse a list of parts into table_name, column_name, and json_path components.

        Args:
            parts: List of address parts (e.g., ["table", "column", "path1", "path2"])

        Returns:
            Tuple of (table_name, column_name, json_path)
        """
        if len(parts) < 2:
            return "", parts[0] if parts else "", None

        table_name = parts[0]
        column_name = parts[1]
        json_path = parts[2:] if len(parts) > 2 else None

        return table_name, column_name, json_path

    @classmethod
    def parse(cls, field_address: str) -> "FieldAddress":
        """
        Parse a field address into components

        Supports formats:
        - "table.column" -> table="table", column="column"
        - "table.json_column.path.subpath" -> table="table", column="json_column", json_path=["path", "subpath"]
        - "table:column" -> table="table", column="column" (alternative format)
        - "column" -> table="", column="column" (requires default table)
        """
        if ":" in field_address:
            # Format: table:column or dataset:collection:field
            # Handle colon-separated format first, then check for dots in the remaining parts
            colon_parts = field_address.split(":")
            if len(colon_parts) >= 2:
                table_name = colon_parts[0]
                remaining = ":".join(colon_parts[1:])  # Join remaining parts

                # Check if the remaining part has dots (JSON path)
                if "." in remaining:
                    # Mixed format: table:column.path1.path2
                    dot_parts = remaining.split(".")
                    parts = [table_name] + dot_parts
                else:
                    # Pure colon format: table:column or table:column:path1:path2
                    parts = colon_parts

                table_name, column_name, json_path = cls._parse_parts_to_components(
                    parts
                )

                return cls(
                    table_name=table_name,
                    column_name=column_name,
                    json_path=json_path,
                    full_address=field_address,
                )

        if "." in field_address:
            # Format: table.column or table.json_column.path.subpath
            parts = field_address.split(".")
            table_name, column_name, json_path = cls._parse_parts_to_components(parts)

            return cls(
                table_name=table_name,
                column_name=column_name,
                json_path=json_path,
                full_address=field_address,
            )

        # Simple column name without table
        return cls(
            table_name="",  # Will need default table
            column_name=field_address,
            json_path=None,
            full_address=field_address,
        )
