from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, root_validator, validator

from fides.api.ops.schemas.saas.saas_config import Header, QueryParam, SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import (
    ConnectorParamRef,
    IdentityParamRef,
)


class StrategyConfiguration(BaseModel):
    """Base class for strategy configuration"""


class UnwrapPostProcessorConfiguration(StrategyConfiguration):
    """Dynamic JSON path access"""

    data_path: str


class FilterPostProcessorConfiguration(StrategyConfiguration):
    """Returns objects where a field has a given value"""

    field: str
    value: Union[str, IdentityParamRef]
    exact: bool = True
    case_sensitive: bool = True


class OffsetPaginationConfiguration(StrategyConfiguration):
    """
    Increases the value of the query param `incremental_param` by the `increment_by` until the `limit` is hit
    or there is no more data available.
    """

    incremental_param: str
    increment_by: int
    limit: Optional[Union[int, ConnectorParamRef]]

    @validator("increment_by")
    def check_increment_by(cls, increment_by: int) -> int:
        if increment_by == 0:
            raise ValueError("'increment_by' cannot be zero")
        if increment_by < 0:
            raise ValueError("'increment_by' cannot be negative")
        return increment_by


class LinkSource(Enum):
    """Locations where the link to the next page may be found."""

    headers = "headers"
    body = "body"


class LinkPaginationConfiguration(StrategyConfiguration):
    """Gets the URL for the next page from the headers or the body."""

    source: LinkSource
    rel: Optional[str]
    path: Optional[str]

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        source = values.get("source")
        if source == LinkSource.headers.value and values.get("rel") is None:
            raise ValueError(
                "The 'rel' value must be specified when accessing the link from the headers"
            )
        if source == LinkSource.body.value and values.get("path") is None:
            raise ValueError(
                "The 'path' value must be specified when accessing the link from the body"
            )
        return values

    class Config:
        """Using enum values"""

        use_enum_values = True


class CursorPaginationConfiguration(StrategyConfiguration):
    """
    Extracts the cursor value from the 'field' of the last object in the array specified by 'data_path'
    """

    cursor_param: str
    field: str


class ApiKeyAuthenticationConfiguration(StrategyConfiguration):
    """
    API key parameter to be added in as a header or query param
    """

    headers: Optional[List[Header]]
    query_params: Optional[List[QueryParam]]

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        headers = values.get("headers")
        query_params = values.get("query_params")

        if not headers and not query_params:
            raise ValueError(
                "At least one 'header' or 'query_param' object must be defined in an 'api_key' auth configuration"
            )

        return values


class BasicAuthenticationConfiguration(StrategyConfiguration):
    """
    Username and password to add basic authentication to HTTP requests
    """

    username: str
    password: Optional[str]


class BearerAuthenticationConfiguration(StrategyConfiguration):
    """
    Token to add as bearer authentication for HTTP requests
    """

    token: str


class QueryParamAuthenticationConfiguration(StrategyConfiguration):
    """
    Value to add as query param for HTTP requests
    """

    name: str
    value: str


class OAuth2BaseConfiguration(StrategyConfiguration):
    """
    OAuth2 endpoints for token retrieval, and token refresh.
    Includes an optional expires_in parameter (in seconds) for OAuth2 integrations that
    do not specify a TTL for the access tokens.
    """

    expires_in: Optional[int]
    token_request: SaaSRequest
    refresh_request: Optional[SaaSRequest]


class OAuth2AuthorizationCodeConfiguration(OAuth2BaseConfiguration):
    """
    The standard OAuth2 configuration but with an additional property to configure
    the authorization request for the Authorization Code flow.
    """

    authorization_request: SaaSRequest
