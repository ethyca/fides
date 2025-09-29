from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import model_validator

from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.strategy_configuration import StrategyConfiguration
from fides.api.util.collection_util import Row


class SupportedDataType(Enum):
    """Supported data types for polling async DSR result requests."""

    json = "json"
    csv = "csv"
    xml = "xml"
    attachment = "attachment"


@dataclass
class PollingResult:
    """
    Flexible result container for async polling operations.
    Handles both structured data and file attachments.
    """

    data: Union[List[Row], bytes]
    result_type: str  # "rows", "attachment", "url"
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class PollingStatusRequest(SaaSRequest):
    """
    Extended SaaSRequest for checking async job status.
    Uses request_override for custom status checking logic or standard fields for simple cases.
    """

    status_path: Optional[str] = None
    status_completed_value: Optional[Union[str, bool, int]] = None

    @model_validator(mode="after")
    def validate_status_fields(self) -> "PollingStatusRequest":
        """Ensure required fields are present unless using an override."""
        if self.request_override:
            return self

        if not self.status_path:
            raise ValueError("status_path is required when request_override is not set")
        if self.status_completed_value is None:
            raise ValueError(
                "status_completed_value is required when request_override is not set"
            )
        return self


class PollingResultRequest(SaaSRequest):
    """
    Extended SaaSRequest for retrieving async job results.
    Uses request_override for custom result retrieval or standard HTTP request for simple cases.
    Data type is automatically inferred from response.
    """

    result_path: Optional[str] = None


class AsyncPollingConfiguration(StrategyConfiguration):
    """
    Simplified configuration for polling async DSR requests.
    The main read request serves as the initial request.
    """

    status_request: PollingStatusRequest
    result_request: PollingResultRequest
