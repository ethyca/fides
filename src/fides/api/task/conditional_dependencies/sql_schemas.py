from typing import Any, Dict

from pydantic import BaseModel, Field


class SQLTranslationError(Exception):
    """Error raised when SQL translation fails"""

    pass


class SQLFieldMapping(BaseModel):
    """Simple mapping from conditional dependency field addresses to SQL column names"""

    field_address: str = Field(description="Field address in conditional dependency")
    column_name: str = Field(description="Corresponding SQL column name")
