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

    consent_v3_encryption_enabled: bool = Field(
        default=True,
        description="Whether to encrypt PII in v3 consent preference records. "
        "Recommended setting is to keep it as true. Set to false to store data in plaintext. "
        "WARNING: Changing this setting requires a data migration in order to keep existing data.",
    )

    identity_enrichment: bool = Field(
        default=False,
        description="Enable identity enrichment before consent propagation. "
        "When enabled, resolves missing email or external_id from stored "
        "preferences before falling back to DB connector queries.",
    )

    identity_enrichment_query_timeout_seconds: int = Field(
        default=30,
        description="Maximum seconds to wait for a single identity enrichment "
        "DB query. Prevents worker threads from blocking indefinitely on slow "
        "or unreachable external databases.",
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
