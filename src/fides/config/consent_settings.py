from pydantic import ConfigDict, Field, model_validator

from .fides_settings import FidesSettings


class ConsentSettings(FidesSettings):
    """Configuration settings for Consent."""

    tcf_enabled: bool = Field(
        default=False, description="Toggle whether TCF is enabled."
    )
    ac_enabled: bool = Field(
        default=False, description="Toggle whether Google AC Mode is enabled."
    )
    model_config = ConfigDict(env_prefix="FIDES__CONSENT__")

    @model_validator(mode="after")
    def validate_fields(self) -> "ConsentSettings":
        """AC mode only works if TCF mode is also enabled"""
        tcf_mode = self.tcf_enabled
        ac_mode = self.ac_enabled

        if ac_mode and not tcf_mode:
            raise ValueError("AC cannot be enabled unless TCF mode is also enabled.")

        return self
