from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__EXECUTION__"


class ExecutionSettings(FidesSettings):
    """Configuration settings for execution."""

    privacy_request_delay_timeout: int = 3600
    task_retry_count: int = 0
    task_retry_delay: int = 1  # In seconds
    task_retry_backoff: int = 1
    subject_identity_verification_required: bool = False
    require_manual_request_approval: bool = False
    masking_strict: bool = True

    class Config:
        env_prefix = ENV_PREFIX
