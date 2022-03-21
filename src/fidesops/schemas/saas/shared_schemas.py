from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


class HTTPMethod(Enum):
    """Enum to represent HTTP Methods"""

    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class SaaSRequestParams(BaseModel):
    """Custom type to represent a SaaS request param"""

    method: HTTPMethod
    path: str
    params: Dict[str, Any]
    body: Optional[str]

    class Config:
        """Using enum values"""

        use_enum_values = True
