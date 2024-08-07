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
    """
    Holds the method, path, headers, query, and body params to build a SaaS HTTP request.
    """

    method: HTTPMethod
    path: str
    headers: Dict[str, Any] = {}
    query_params: Dict[str, Any] = {}
    body: Optional[str]

    class Config:
        """Using enum values"""

        use_enum_values = True


class ConnectorParamRef(BaseModel):
    """A reference to a value in the connector params (by name)"""

    connector_param: Any


class IdentityParamRef(BaseModel):
    """A reference to the identity type in the filter Post Processor Config"""

    identity: str
