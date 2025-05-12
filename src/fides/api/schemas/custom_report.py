from enum import Enum
from typing import Any, Dict, Optional, Set

from pydantic import Field

from fides.api.schemas.base_class import FidesSchema


class ReportType(str, Enum):
    """Enum for custom report types."""

    datamap = "datamap"
    privacy_request = "privacy_request"


class ColumnMapItem(FidesSchema):
    """A map between column keys and custom labels."""

    label: Optional[str] = Field(
        default=None, description="The custom label for the column"
    )
    enabled: Optional[bool] = Field(
        default=True, description="Whether the column is shown"
    )


class CustomReportConfig(FidesSchema):
    """The configuration for a custom report."""

    table_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible dictionary storing UI-specific table state data without a fixed schema",
    )
    column_map: Dict[str, ColumnMapItem] = Field(
        default_factory=dict, description="A map between column keys and custom labels"
    )

    @property
    def columns_to_skip(self) -> Set[str]:
        return {
            key
            for key, value in self.column_map.items()  # pylint: disable=no-member
            if value.enabled is False
        }

    @property
    def custom_column_labels(self) -> Dict[str, str]:
        return {
            key: value.label
            for key, value in self.column_map.items()  # pylint: disable=no-member
            if value.label
        }
