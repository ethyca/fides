from enum import Enum
from io import BufferedReader
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict

RequestFile = Tuple[str, Tuple[str, BufferedReader, str]]


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
    body: Optional[str] = None
    files: Optional[List[RequestFile]] = None
    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class ConnectorParamRef(BaseModel):
    """A reference to a value in the connector params (by name)"""

    connector_param: Any = None


class IdentityParamRef(BaseModel):
    """A reference to the identity type in the filter Post Processor Config"""

    identity: str


class DatasetRef(BaseModel):
    """A reference to the dataset field in the filter Post Processor Config"""

    dataset_reference: str


class ConsentPropagationStatus(Enum):
    """
    An enum for the different statuses that can be returned from a consent propagation request.
    """

    executed = "executed"
    no_update_needed = "no_update_needed"
    missing_data = "missing_data"
