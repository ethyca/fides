from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings


class ConsentSettings(FidesSettings):
    """Configuration settings for Consent."""

    tcf_enabled: bool = Field(
        default=False, description="Toggle whether TCF is enabled."
    )
    ac_enabled: bool = Field(
        default=False, description="Toggle whether Google AC Mode is enabled."
    )

    override_vendor_purposes: bool = Field(
        default=False,
        description="Whether or not vendor purposes can be globally overridden.",
    )
    model_config = SettingsConfigDict(env_prefix="FIDES__CONSENT__")

    @model_validator(mode="after")
    def validate_fields(self) -> "ConsentSettings":
        """AC mode only works if TCF mode is also enabled"""
        tcf_mode = self.tcf_enabled
        ac_mode = self.ac_enabled
        override_vendor_purposes = self.override_vendor_purposes

        if ac_mode and not tcf_mode:
            raise ValueError("AC cannot be enabled unless TCF mode is also enabled.")

        if override_vendor_purposes and not tcf_mode:
            raise ValueError(
                "Override vendor purposes cannot be true unless TCF mode is also enabled."
            )

        return self
