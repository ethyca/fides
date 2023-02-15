from os import getenv

DEFAULT_CONFIG_PATH = ".fides/fides.toml"
DEFAULT_CONFIG_PATH_ENV_VAR = "FIDES__CONFIG_PATH"


def get_test_mode() -> bool:
    test_mode = getenv("FIDES__TEST_MODE", "").lower() == "true"
    return test_mode


def get_dev_mode() -> bool:
    dev_mode = getenv("FIDES__DEV_MODE", "").lower() == "true"
    return dev_mode


CONFIG_KEY_ALLOWLIST = {
    "cli": ["server_host", "server_port"],
    "user": ["analytics_opt_out"],
    "logging": ["level"],
    "database": [
        "server",
        "user",
        "port",
        "db",
        "test_db",
        "api_engine_pool_size",
        "api_engine_max_overflow",
        "task_engine_pool_size",
        "task_engine_max_overflow",
    ],
    "notifications": [
        "send_request_completion_notification",
        "send_request_receipt_notification",
        "send_request_review_notification",
        "notification_service_type",
    ],
    "redis": [
        "host",
        "port",
        "charset",
        "decode_responses",
        "default_ttl_seconds",
        "db_index",
    ],
    "security": [
        "cors_origins",
        "encoding",
        "oauth_access_token_expire_minutes",
    ],
    "execution": [
        "task_retry_count",
        "task_retry_delay",
        "task_retry_backoff",
        "require_manual_request_approval",
    ],
}
