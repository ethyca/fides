from enum import Enum
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, validator, root_validator


class StrategyConfiguration(BaseModel):
    """Base class for strategy configuration"""


class UnwrapPostProcessorConfiguration(StrategyConfiguration):
    """Dynamic JSON path access"""

    data_path: str


class IdentityParamRef(BaseModel):
    """A reference to the identity type in the filter Post Processor Config"""

    identity: str


class ConnectorParamRef(BaseModel):
    """A reference to a value in the connector params (by name)"""

    connector_param: Any


class FilterPostProcessorConfiguration(StrategyConfiguration):
    """Returns objects where a field has a given value"""

    field: str
    value: Union[str, IdentityParamRef]


class OffsetPaginationConfiguration(StrategyConfiguration):
    """
    Increases the value of the query param `incremental_param` by the `increment_by` until the `limit` is hit
    or there is no more data available.
    """

    incremental_param: str
    increment_by: int
    limit: Union[int, ConnectorParamRef]

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
