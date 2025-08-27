from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__EXECUTION__"


class ExecutionSettings(FidesSettings):
    """Configuration settings for DSR execution."""

    privacy_request_delay_timeout: int = Field(
        default=3600,
        description="The amount of time to wait for actions which delay privacy requests (e.g., pre- and post-processing webhooks).",
    )
    require_manual_request_approval: bool = Field(
        default=False,
        description="Whether access and erasure privacy requests require explicit approval to execute. Consent privacy requests are always auto-approved.",
    )
    subject_identity_verification_required: bool = Field(
        default=False,
        description="Whether privacy requests require user identity verification.",
    )
    disable_consent_identity_verification: Optional[bool] = Field(
        default=None,
        description="Allows selective disabling of identity verification specifically for consent requests. Identity verification for consent requests will be enabled if subject_identity_verification_required is set to true and this setting is empty or false.",
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
    request_task_ttl: int = Field(
        default=604800,
        description="The number of seconds a request task should live.",
    )
    state_polling_interval: int = Field(
        default=30,
        description="Seconds between polling for Privacy Requests that should change state",
    )
    interrupted_task_requeue_interval: int = Field(
        default=300,
        description="Seconds between polling for interrupted tasks to requeue",
    )
    privacy_request_requeue_retry_count: int = Field(
        default=3,
        description="The number of times a privacy request will be requeued when its tasks are interrupted before being marked as error",
    )
    async_tasks_status_polling_interval_seconds: int = Field(
        default=3600,
        description="Seconds between polling for async tasks to requeue",
    )
    use_dsr_3_0: bool = Field(
        default=False,
        description="Temporary flag to switch to using DSR 3.0 to process your tasks.",
    )
    erasure_request_finalization_required: bool = Field(
        default=False,
        description="Whether erasure requests require an additional finalization step after all collections have been executed.",
    )
    fuzzy_search_enabled: bool = Field(
        default=True,
        description="Whether fuzzy search is enabled for privacy request lookups.",
    )
    email_send_cron_expression: str = Field(
        default="0 12 * * mon",
        description="The cron expression to send batch emails for DSR email integration. Defaults to weekly on Mondays at 12pm (noon).",
    )
    email_send_timezone: str = Field(
        default="US/Eastern",
        description="The timezone to send batch emails for DSR email integration.",
    )
    memory_watchdog_enabled: bool = Field(
        default=False,
        description="Whether the memory watchdog is enabled to monitor and gracefully terminate tasks that approach memory limits.",
    )
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
