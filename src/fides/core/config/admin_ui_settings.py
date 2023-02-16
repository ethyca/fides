from .fides_settings import FidesSettings
from pydantic import Field


class AdminUISettings(FidesSettings):
    """Configuration settings for Analytics variables."""

    enabled: bool = Field(
        default=True, description="Toggle whether the Admin UI is served."
    )

    class Config:
        env_prefix = "FIDES__ADMIN_UI__"
