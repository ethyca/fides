from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.sql.elements import TextClause


class SQLTranslationError(Exception):
    """Error raised when SQL translation fails"""

    pass


class SQLFieldMapping(BaseModel):
    """Simple mapping from conditional dependency field addresses to SQL column names"""

    field_address: str = Field(description="Field address in conditional dependency")
    column_name: str = Field(description="Corresponding SQL column name")


class SQLQueryResult(BaseModel):
    """Result of SQL query generation"""

    query: str = Field(description="Generated SQL query string")
    parameters: Dict[str, Any] = Field(description="Query parameters")


class SQLTranslationConfig(BaseModel):
    """Configuration for SQL translation"""

    table_name: str = Field(description="Target table name")
    field_mappings: Dict[str, str] = Field(default_factory=dict, description="Field address to column name mappings")
    schema_name: Optional[str] = Field(default=None, description="Optional schema name")
    enable_json_path: bool = Field(default=True, description="Enable PostgreSQL JSON path operators")

    @property
    def qualified_table_name(self) -> str:
        """Get fully qualified table name with schema if specified"""
        if self.schema_name:
            return f"{self.schema_name}.{self.table_name}"
        return self.table_name


class SQLDataType(BaseModel):
    """SQL data type information for better query generation"""

    column_name: str = Field(description="Column name")
    data_type: str = Field(description="SQL data type (e.g., 'integer', 'text', 'jsonb', 'text[]')")
    is_array: bool = Field(default=False, description="Whether this is an array type")
    is_json: bool = Field(default=False, description="Whether this is a JSON/JSONB type")
