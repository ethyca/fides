from pydantic import Field

from .fides_settings import FidesSettings


class ConsentSettings(FidesSettings):
    """Configuration settings for Consent."""

    tcf_enabled: bool = Field(
        default=False, description="Toggle whether TCF is enabled."
    )
    ac_enabled: bool = Field(
        default=False, description="Toggle whether Google AC Mode is enabled."
    )

    class Config:
        env_prefix = "FIDES__CONSENT__"
