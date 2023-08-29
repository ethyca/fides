from typing import Optional

import validators
from pydantic import Field, validator

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__JOBS__"


class JobSettings(FidesSettings):
    """Configuration settings for job scheduling."""

    # System change digest
    system_change_webhook_url: Optional[str] = Field(
        default=None,
        description="The URL to send the system change digest to. Defaults to None.",
    )

    @validator("system_change_webhook_url", pre=True)
    @classmethod
    def validate_system_change_webhook_url(cls, value: Optional[str]) -> Optional[str]:
        """
        The value should be a valid URL or None
        """
        if value is None:
            return None

        if validators.url(value):
            return value
        else:
            raise ValueError("Invalid system change webhook URL")

    class Config:
        env_prefix = ENV_PREFIX
