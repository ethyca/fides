from pydantic import Field

from .fides_settings import FidesSettings


class ConsentSettings(FidesSettings):
    """Configuration settings for Consent."""

    tcf_enabled: bool = Field(
        default=False, description="Toggle whether TCF is enabled."
    )

    class Config:
        env_prefix = "FIDES__CONSENT__"
