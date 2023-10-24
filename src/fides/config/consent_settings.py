from typing import Any, Dict

from pydantic import Field, root_validator

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

    @root_validator
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """AC mode only works if TCF mode is also enabled"""
        tcf_mode = values.get("tcf_enabled")
        ac_mode = values.get("ac_enabled")

        if ac_mode and not tcf_mode:
            raise ValueError("AC cannot be enabled unless TCF mode is also enabled.")

        return values
