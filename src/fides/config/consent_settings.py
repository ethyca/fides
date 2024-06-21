from typing import Any, Dict

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

    override_vendor_purposes: bool = Field(
        default=False,
        description="Whether or not vendor purposes can be globally overridden.",
    )
    model_config = ConfigDict(env_prefix="FIDES__CONSENT__")

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """AC mode only works if TCF mode is also enabled"""
        tcf_mode = values.get("tcf_enabled")
        ac_mode = values.get("ac_enabled")
        override_vendor_purposes = values.get("override_vendor_purposes")

        if ac_mode and not tcf_mode:
            raise ValueError("AC cannot be enabled unless TCF mode is also enabled.")

        if override_vendor_purposes and not tcf_mode:
            raise ValueError(
                "Override vendor purposes cannot be true unless TCF mode is also enabled."
            )

        return values