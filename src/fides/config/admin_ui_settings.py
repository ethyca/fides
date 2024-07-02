from typing import Optional

from pydantic import AnyHttpUrl, Field

from .fides_settings import FidesSettings


class AdminUISettings(FidesSettings):
    """Configuration settings for the Admin UI."""

    enabled: bool = Field(
        default=True, description="Toggle whether the Admin UI is served."
    )
    url: Optional[AnyHttpUrl] = Field(
        default=None, description="The base URL for the Admin UI."
    )

    class Config:
        env_prefix = "FIDES__ADMIN_UI__"
