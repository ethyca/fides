from pydantic import ConfigDict, Field

from .fides_settings import FidesSettings


class AdminUISettings(FidesSettings):
    """Configuration settings for the Admin UI."""

    enabled: bool = Field(
        default=True, description="Toggle whether the Admin UI is served."
    )
    model_config = ConfigDict(env_prefix="FIDES__ADMIN_UI__")
