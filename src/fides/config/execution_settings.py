from pydantic import Field

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__EXECUTION__"


class ExecutionSettings(FidesSettings):
    """Configuration settings for DSR execution."""

    masking_strict: bool = Field(
        default=True,
        description="If set to True, only use UPDATE requests to mask data. If False, Fides will use any defined DELETE or GDPR DELETE endpoints to remove PII, which may extend beyond the specific data categories that configured in your execution policy.",
    )
    privacy_request_delay_timeout: int = Field(
        default=3600,
        description="The amount of time to wait for actions which delay privacy requests (e.g., pre- and post-processing webhooks).",
    )
    require_manual_request_approval: bool = Field(
        default=False,
        description="Whether privacy requests require explicit approval to execute.",
    )
    subject_identity_verification_required: bool = Field(
        default=False,
        description="Whether privacy requests require user identity verification.",
    )
    disable_consent_identity_verification: bool = Field(
        default=None,
        description="Allows selective disabling of identity verification specifically for consent requests. Identity verification for consent requests will be enabled if subject_identity_verification_required is set to true and this setting is empty or false.",
        exclude=True,
    )
    task_retry_backoff: int = Field(
        default=1,
        description="The backoff factor for retries, to space out repeated retries.",
    )
    task_retry_count: int = Field(
        default=0, description="The number of times a failed request will be retried."
    )
    task_retry_delay: int = Field(
        default=1, description="The delays between retries in seconds."
    )
    allow_custom_privacy_request_field_collection: bool = Field(
        default=False,
        description="Allows the collection of custom privacy request fields from incoming privacy requests.",
    )
    allow_custom_privacy_request_fields_in_request_execution: bool = Field(
        default=False,
        description="Allows custom privacy request fields to be used in request execution.",
    )

    class Config:
        env_prefix = ENV_PREFIX
