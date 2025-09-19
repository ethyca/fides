import zoneinfo
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fides.api.models.digest.digest_config import DigestType
from fides.api.schemas.messaging.messaging import MessagingMethod


class DigestConfigBase(BaseModel):
    """Base schema for digest configuration."""

    digest_type: DigestType = Field(description="Type of digest")
    name: str = Field(
        min_length=1, max_length=255, description="Human-readable name for the digest"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Description of the digest"
    )
    enabled: bool = Field(default=True, description="Whether digest is enabled")
    messaging_service_type: MessagingMethod = Field(
        default=MessagingMethod.EMAIL, description="Messaging service type"
    )
    cron_expression: Optional[str] = Field(
        None, max_length=100, description="Custom cron expression for scheduling"
    )
    timezone: str = Field(
        default="US/Eastern", max_length=50, description="Timezone for scheduling"
    )
    config_metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata for the digest"
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, value: Optional[str]) -> Optional[str]:
        """Validate cron expression format."""
        if value is None:
            return value

        # Basic cron validation (5 or 6 fields)
        parts = value.strip().split()
        if len(parts) not in [5, 6]:
            raise ValueError("Cron expression must have 5 or 6 fields")

        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Validate timezone string."""
        try:
            zoneinfo.ZoneInfo(value)
        except zoneinfo.ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {value}")
        return value
