from typing import Optional

from pydantic import BaseModel, Field

from fides.api.task.conditional_dependencies.schemas import Operator


def _handle_list_contains(col, val):
    """
    Handle list_contains operator for different scenarios:
    - If val is a list: check if column value is IN the list
    - If val is a single value: check if column contains the value (for arrays/JSON) or use LIKE (for strings)
    """
    if isinstance(val, list):
        # Column value should be in the provided list
        return col.in_(val)
    else:
        # Single value - check if column contains it
        # For JSON/array columns, this would need special handling
        # For now, fall back to LIKE for string matching
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
    Operator.list_contains: lambda col, val: _handle_list_contains(col, val),
    Operator.not_in_list: lambda col, val: ~_handle_list_contains(col, val),
}


class SQLTranslationError(Exception):
    """Error raised when SQL translation fails"""


class FieldAddress(BaseModel):
    """Parsed field address with table and column information"""

    table_name: str = Field(description="Table name extracted from field address")
    column_name: str = Field(description="Base column name without JSON path")
    json_path: Optional[list[str]] = Field(
        default=None, description="JSON path components if this is a JSON field"
    )
    full_address: str = Field(description="Original field address string")

    @property
    def is_json_path(self) -> bool:
        """Whether this field address includes a JSON path"""
        return self.json_path is not None and len(self.json_path) > 0

    def __hash__(self) -> int:
        """Make FieldAddress hashable for use in sets"""
        return hash(
            (
                self.table_name,
                self.column_name,
                tuple(self.json_path) if self.json_path else None,
            )
        )

    def __eq__(self, other) -> bool:
        """Enable equality comparison for FieldAddress objects"""
        if not isinstance(other, FieldAddress):
            return False
        return (
            self.table_name == other.table_name
            and self.column_name == other.column_name
            and self.json_path == other.json_path
        )

    @property
    def base_field_name(self) -> str:
        """Get the base field name for SELECT clause (without JSON path operators)"""
        return self.column_name

    def to_sql_column(self, enable_json_operators: bool = True) -> str:
        """
        Convert field address to PostgreSQL column reference

        Args:
            enable_json_operators: Whether to use PostgreSQL JSON operators for JSON paths

        Returns:
            SQL column reference string
        """
        if not self.is_json_path or not enable_json_operators:
            return self.column_name

        # Build PostgreSQL JSON path: column->'path'->'path'->>'final_path'
        if len(self.json_path) == 1:
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
