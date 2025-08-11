from typing import Optional

from pydantic import Field, SerializeAsAny
from pydantic_settings import SettingsConfigDict

from fides.api.custom_types import AnyHttpUrlStringRemovesSlash

from .fides_settings import FidesSettings


class PrivacyCenterSettings(FidesSettings):
    """Configuration settings for the Privacy Center."""

    url: SerializeAsAny[Optional[AnyHttpUrlStringRemovesSlash]] = Field(
        default=None, description="The base URL for the Privacy Center."
    )
    model_config = SettingsConfigDict(env_prefix="FIDES__PRIVACY_CENTER__")
