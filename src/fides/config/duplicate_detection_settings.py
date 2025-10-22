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

    auto_detect_on_creation: bool = Field(
        default=True,
        description="Whether to automatically detect duplicates when a request is created.",
    )

    exclude_duplicates_by_default: bool = Field(
        default=True,
        description="Whether to hide duplicates by default in list views.",
    )

    model_config = SettingsConfigDict(env_prefix="FIDES__DUPLICATE_DETECTION__")
