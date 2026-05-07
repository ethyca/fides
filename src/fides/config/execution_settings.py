from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__EXECUTION__"


class ExecutionSettings(FidesSettings):
    """Configuration settings for DSR execution."""

    privacy_request_delay_timeout: int = Field(
        default=3600,
        description="The amount of time to wait, in minutes, for actions which delay privacy requests (e.g., pre- and post-processing webhooks). Default: 3600 minutes",
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
    async_polling_interval_hours: int = Field(
        default=1,
        description="Hours between status checks for async tasks",
    )
    async_polling_request_timeout_days: int = Field(
        default=30,
        description="Maximum time in days to wait for an async polling request to complete before timing out",
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
    ignore_dsr_celery_task_results: bool = Field(
        default=False,
        description=(
            "When true, DSR-queue Celery publishes pass ignore_result=True (no result-backend "
            "tombstones for run_privacy_request or queue_request_task dispatches). Default false "
            "preserves current result storage. Set via FIDES__EXECUTION__IGNORE_DSR_CELERY_TASK_RESULTS."
        ),
    )
    use_legacy_traversal: bool = Field(
        default=False,
        description="When enabled, falls back to the legacy traversal algorithm. Intended as a temporary safety net in case of regressions with the optimized traversal.",
    )
    task_soft_time_limit_seconds: int = Field(
        default=0,
        description="Soft time limit in seconds for privacy request Celery tasks. "
        "When exceeded, SoftTimeLimitExceeded is raised and the full stack trace is logged. "
        "Set to 0 to disable (default).",
    )
    jira_polling_interval_minutes: int = Field(
        default=10,
        description="Minutes between polling Jira for ticket status updates.",
    )
    terminal_dsr_redis_cache_cleanup_enabled: bool = Field(
        default=False,
        description="Application preference: when true, the periodic terminal DSR Redis cache "
        "cleanup task may run (still requires terminal_dsr_redis_cache_cleanup_interval_minutes "
        "> 0 for the scheduler job to be registered). Default: off.",
    )
    terminal_dsr_redis_cache_cleanup_interval_minutes: int = Field(
        default=0,
        description="Minutes between periodic Redis cache cleanups for terminal privacy "
        "requests (complete/canceled, plus optional statuses). Set to 0 to disable registering "
        "the scheduler job. When registered, execution also requires "
        "terminal_dsr_redis_cache_cleanup_enabled.",
    )
    terminal_dsr_redis_cache_cleanup_dry_run: bool = Field(
        default=True,
        description="When true, the cleanup job re-checks Postgres eligibility but does not "
        "delete Redis keys (use for rollout).",
    )
    terminal_dsr_redis_cache_cleanup_dry_run_probe_redis: bool = Field(
        default=False,
        description="When dry_run is true and this is true, count Redis keys per request "
        "(uses SCAN/get_all_keys; may add load in large batches).",
    )
    terminal_dsr_redis_cache_cleanup_staleness_minutes: int = Field(
        default=30,
        description="Only privacy requests whose updated_at is older than this many minutes "
        "are eligible, to reduce races with trailing cache writes.",
    )
    terminal_dsr_redis_cache_cleanup_batch_size: int = Field(
        default=50,
        description="Max privacy requests to process per database batch (keyset pagination).",
    )
    terminal_dsr_redis_cache_cleanup_batch_sleep_seconds: float = Field(
        default=0.5,
        description="Base delay between batches; a random jitter up to this value is added.",
    )
    terminal_dsr_redis_cache_cleanup_include_denied_and_duplicate: bool = Field(
        default=True,
        description="Treat denied and duplicate statuses as terminal for Redis cleanup.",
    )
    terminal_dsr_redis_cache_cleanup_include_error: bool = Field(
        default=False,
        description="Include error status (clears Redis-only resume/operator context). "
        "Destructive for workflows that rely on stale error cache—enable only with care.",
    )
    terminal_dsr_redis_cache_cleanup_lock_timeout_seconds: int = Field(
        default=1800,
        ge=60,
        description="Redis lock TTL (seconds) for the terminal DSR Redis cache cleanup job "
        "to prevent overlapping runs. Default 1800 (30 minutes). Override via env "
        "FIDES__EXECUTION__TERMINAL_DSR_REDIS_CACHE_CLEANUP_LOCK_TIMEOUT_SECONDS or "
        "application config execution.terminal_dsr_redis_cache_cleanup_lock_timeout_seconds.",
    )
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
