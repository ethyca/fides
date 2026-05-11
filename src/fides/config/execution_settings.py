from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__EXECUTION__"


class DsrCacheSweeperSettings(BaseModel):
    """DSR cache sweeper: periodic Redis cleanup for terminal privacy requests."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(
        default=False,
        description=(
            "When true, the periodic cleanup task may run (still requires interval_minutes > 0 "
            "for the scheduler job to be registered). Default off."
        ),
    )
    interval_minutes: int = Field(
        default=0,
        description=(
            "Minutes between periodic Redis cache cleanups for terminal privacy requests "
            "(complete/canceled, plus optional statuses). Set to 0 to disable registering "
            "the scheduler job. When registered, execution also requires enabled."
        ),
    )
    staleness_minutes: int = Field(
        default=30,
        description=(
            "Only privacy requests whose updated_at is older than this many minutes "
            "are eligible, to reduce races with trailing cache writes."
        ),
    )
    batch_size: int = Field(
        default=10000,
        ge=10,
        description=(
            "Max privacy requests to process per database batch (keyset pagination). "
            "Minimum 10; increase for fewer round-trips on large backlogs."
        ),
    )
    batch_sleep_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Base delay between database batches (seconds); a random jitter from 0 up to "
            "this value is added. Default 0 (disabled). Increase to lightly yield between "
            "pages if needed as a safety valve under load."
        ),
    )
    include_denied_and_duplicate: bool = Field(
        default=True,
        description="Treat denied and duplicate statuses as terminal for Redis cleanup.",
    )
    include_error: bool = Field(
        default=False,
        description=(
            "Include error status (clears Redis-only resume/operator context). "
            "Destructive for workflows that rely on stale error cache—enable only with care."
        ),
    )
    lock_timeout_seconds: int = Field(
        default=1800,
        ge=60,
        description=(
            "Redis lock TTL (seconds) for the sweeper job to prevent overlapping runs. "
            "Default 1800 (30 minutes). Nested env: "
            "FIDES__EXECUTION__DSR_CACHE_SWEEPER__LOCK_TIMEOUT_SECONDS. "
            "Legacy flat keys FIDES__EXECUTION__TERMINAL_DSR_REDIS_CACHE_CLEANUP_* and "
            "FIDES__EXECUTION__DSR_CACHE_SWEEPER_* are still accepted via model validation."
        ),
    )
    single_pass_redis_sweep: bool = Field(
        default=True,
        description=(
            "When true (default), use one Redis SCAN over the keyspace plus a temporary "
            "maintenance set for eligible IDs. Set false to fall back to per-request "
            "``DSRCacheStore.clear()`` (legacy, more Redis round-trips)."
        ),
    )
    maintenance_set_ttl_seconds: int = Field(
        default=14400,
        ge=300,
        description=(
            "TTL (seconds) on the Redis staging set of eligible privacy request IDs. "
            "Should exceed worst-case sweep duration and the Celery lock TTL so a crashed "
            "worker does not leave the set forever. Default 4 hours."
        ),
    )
    maintenance_set_key: str = Field(
        default="__maintenance:dsr_cache_sweeper:eligible_ids",
        description=(
            "Redis key for the temporary eligible-ID set (SADD/SMISMEMBER). Override for "
            "multi-tenant or test isolation."
        ),
    )
    redis_scan_count: int = Field(
        default=750,
        ge=10,
        le=10000,
        description="Hint passed to Redis SCAN COUNT per iteration (single-pass mode).",
    )
    redis_delete_batch_size: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Max keys per pipeline UNLINK/DEL batch in single-pass mode.",
    )
    membership_lookup_batch_size: int = Field(
        default=2048,
        ge=50,
        le=20000,
        description=(
            "How many staging-set membership checks (SMISMEMBER commands) to send in each "
            "Redis pipeline round trip while scanning keys in single-pass mode. Default "
            "2048 balances fewer round trips against predictable latency. Override only if "
            "you measure a need."
        ),
    )


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
    dsr_cache_sweeper: DsrCacheSweeperSettings = Field(
        default_factory=DsrCacheSweeperSettings,
        description=(
            "DSR cache sweeper (terminal privacy request Redis cache). Nested env vars: "
            "FIDES__EXECUTION__DSR_CACHE_SWEEPER__<FIELD>. Legacy flat "
            "terminal_dsr_redis_cache_cleanup_* / dsr_cache_sweeper_* keys and legacy nested "
            "terminal_dsr_redis_cache_cleanup objects are folded into dsr_cache_sweeper."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _nest_dsr_cache_sweeper_keys(cls, data: Any) -> Any:
        """Fold legacy nested/flat execution keys into ``dsr_cache_sweeper``."""
        if not isinstance(data, dict):
            return data

        merged: dict[str, Any] = {}
        if isinstance(data.get("dsr_cache_sweeper"), dict):
            merged.update(data["dsr_cache_sweeper"])

        legacy_nested = data.pop("terminal_dsr_redis_cache_cleanup", None)
        if isinstance(legacy_nested, dict):
            merged = {**legacy_nested, **merged}

        prefixes = ("terminal_dsr_redis_cache_cleanup_", "dsr_cache_sweeper_")
        for key in list(data.keys()):
            for prefix in prefixes:
                if key.startswith(prefix) and key not in (
                    "terminal_dsr_redis_cache_cleanup",
                    "dsr_cache_sweeper",
                ):
                    suffix = key[len(prefix) :]
                    if suffix:
                        merged[suffix] = data.pop(key)
                    break

        # Legacy rollout flags removed from the model; drop so extra=forbid passes.
        for _obsolete in ("dry_run", "dry_run_probe_redis"):
            merged.pop(_obsolete, None)

        if merged:
            data["dsr_cache_sweeper"] = merged
        else:
            data.pop("dsr_cache_sweeper", None)

        data.pop("terminal_dsr_redis_cache_cleanup", None)
        return data

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
    )
