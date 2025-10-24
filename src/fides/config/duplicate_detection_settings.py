from typing import List

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings


class DuplicateDetectionSettings(FidesSettings):
    """Configuration settings for Duplicate Privacy Request Detection."""

    enabled: bool = Field(
        default=False,
        description="Whether duplicate detection is enabled. Disabled by default.",
    )

    time_window_days: int = Field(
        default=365,
        description="Time window in days for duplicate detection. Default is 1 year.",
        ge=1,
        le=3650,  # Max 10 years
    )

    match_identity_fields: List[str] = Field(
        default=["email"],
        description="Identity field names to match on for duplicate detection (e.g., 'email', 'phone_number'). Default is email only.",
    )

    model_config = SettingsConfigDict(
        env_prefix="FIDES__PRIVACY_REQUEST_DUPLICATE_DETECTION__"
    )
