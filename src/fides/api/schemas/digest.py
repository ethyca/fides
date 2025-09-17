from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

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
