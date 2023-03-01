from os import getenv

DEFAULT_CONFIG_PATH = ".fides/fides.toml"
DEFAULT_CONFIG_PATH_ENV_VAR = "FIDES__CONFIG_PATH"


def replace_config_value(
    fides_directory_location: str, key: str, old_value: str, new_value: str
) -> None:
    """Use string replacment to update a value in the fides.toml"""

    # This matches the logic used in `docs.py`
    fides_dir_name = ".fides"
    fides_dir_path = f"{fides_directory_location}/{fides_dir_name}"
    config_file_name = "fides.toml"
    config_path = f"{fides_dir_path}/{config_file_name}"

    with open(config_path, "r", encoding="utf8") as config_file:
        previous_config = config_file.read()
        new_config = previous_config.replace(
            f"{key} = {old_value}", f"{key} = {new_value}"
        )

    with open(config_path, "w", encoding="utf8") as config_file:
        config_file.write(new_config)

    print(f"Config key: {key} value changed: {old_value} -> {new_value}")


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
        "subject_identity_verification_required",
    ],
    "storage": [
        "active_default_storage_type",
    ],
}
