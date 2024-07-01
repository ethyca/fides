from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings


class AdminUISettings(FidesSettings):
    """Configuration settings for the Admin UI."""

    enabled: bool = Field(
        default=True, description="Toggle whether the Admin UI is served."
    )
    model_config = SettingsConfigDict(env_prefix="FIDES__ADMIN_UI__")
