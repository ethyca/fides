from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import FidesSchema


class ReportType(str, Enum):
    """Enum for custom report types."""

    datamap = "datamap"
    privacy_request = "privacy_request"


class CustomReportConfig(FidesSchema):
    """The configuration for a custom report."""

    table_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible dictionary storing UI-specific table state data without a fixed schema",
    )
    column_map: Dict[str, str] = Field(
        default_factory=dict, description="A map between column keys and custom labels"
    )
