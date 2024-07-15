from typing import Optional

from pydantic import Field, SerializeAsAny
from pydantic_settings import SettingsConfigDict

from fideslang.validation import AnyHttpUrlString
from .fides_settings import FidesSettings


class AdminUISettings(FidesSettings):
    """Configuration settings for the Admin UI."""

    enabled: bool = Field(
        default=True, description="Toggle whether the Admin UI is served."
    )
    url: SerializeAsAny[Optional[AnyHttpUrlString]] = Field(
        default=None, description="The base URL for the Admin UI."
    )
    model_config = SettingsConfigDict(env_prefix="FIDES__ADMIN_UI__")
