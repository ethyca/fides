from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, text

from fides.api.task.conditional_dependencies.schemas import Operator


class SQLTranslationError(Exception):
    """Error raised when SQL translation fails"""


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
        # This is a PostgreSQL array - use the @> containment operator
        # @> checks if the left array contains the right array/element
        # Create a PostgreSQL array literal with proper type casting
        # Cast to character varying[] to match the column type
        array_literal = text(f"ARRAY['{val}']::character varying[]")
        return col.op("@>")(array_literal)

    # Try JSON containment for JSONB/JSON columns
    try:
        return col.contains(val)
    except Exception:
        # Fallback to LIKE for string columns
        return col.like(f"%{val}%")


OPERATOR_MAP = {
    Operator.eq: lambda col, val: col == val,
    Operator.neq: lambda col, val: col != val,
    Operator.lt: lambda col, val: col < val,
    Operator.lte: lambda col, val: col <= val,
    Operator.gt: lambda col, val: col > val,
    Operator.gte: lambda col, val: col >= val,
    Operator.contains: lambda col, val: col.like(f"%{val}%"),
    Operator.starts_with: lambda col, val: col.like(f"{val}%"),
    Operator.ends_with: lambda col, val: col.like(f"%{val}"),
    Operator.exists: lambda col, val: col.isnot(None),
    Operator.not_exists: lambda col, val: col.is_(None),
    Operator.list_contains: _handle_list_contains,
    Operator.not_in_list: lambda col, val: ~_handle_list_contains(col, val),
}


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
            raise SQLTranslationError("Field address internal error.")

        # Build PostgreSQL JSON path: column->'path'->'path'->>'final_path'
        if self.json_path and len(self.json_path) == 1:
            # Simple case: column->>'field'
            return f"{self.column_name}->>'{self.json_path[0]}'"

        # Complex case: column->'field'->'field'->>'final_field'
        path_parts = []
        # All but last use -> operator
        for part in self.json_path[:-1]:
            path_parts.append(f"->'{part}'")
        # Last part uses ->> operator (returns text)
        path_parts.append(f"->>'{self.json_path[-1]}'")

        return f"{self.column_name}{''.join(path_parts)}"

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
            parts = field_address.split(":")
            if len(parts) >= 2:
                table_name = parts[0]
                column_name = ":".join(parts[1:])  # Join remaining parts
                return cls(
                    table_name=table_name,
                    column_name=column_name,
                    json_path=None,
                    full_address=field_address,
                )

        if "." in field_address:
            # Format: table.column or table.json_column.path.subpath
            parts = field_address.split(".")
            if len(parts) >= 2:
                table_name = parts[0]
                if len(parts) == 2:
                    # Simple: table.column
                    column_name = parts[1]
                    json_path = None
                else:
                    # JSON path: table.json_column.path.subpath
                    column_name = parts[1]  # Base column name
                    json_path = parts[2:]  # JSON path components

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
