from enum import Enum
from typing import Optional

from pydantic import Field, SerializeAsAny
from pydantic_settings import SettingsConfigDict

from fides.api.custom_types import AnyHttpUrlStringRemovesSlash

from .fides_settings import FidesSettings


class ErrorNotificationMode(str, Enum):
    CONSOLE_ONLY = "console_only"
    TOAST = "toast"


class AdminUISettings(FidesSettings):
    """Configuration settings for the Admin UI."""

    enabled: bool = Field(
        default=True, description="Toggle whether the Admin UI is served."
    )
    url: SerializeAsAny[Optional[AnyHttpUrlStringRemovesSlash]] = Field(
        default=None, description="The base URL for the Admin UI."
    )
    max_privacy_request_download_rows: int = Field(
        default=100000,
        description="The maximum number of rows permitted to be returned in a privacy request report download",
    )
    error_notification_mode: Optional[str] = Field(
        default=ErrorNotificationMode.CONSOLE_ONLY.value,
        description="This setting controls how errors are notified to users.",
    )
    model_config = SettingsConfigDict(env_prefix="FIDES__ADMIN_UI__")
