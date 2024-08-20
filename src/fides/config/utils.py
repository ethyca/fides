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


# NOTE: allowlist additions should be made with care!
# Any updates to this list _need_ to be reviewed by the Ethyca security team
CONFIG_KEY_ALLOWLIST = {
    "user": ["analytics_opt_out"],
    "logging": ["level"],
    "notifications": [
        "send_request_completion_notification",
        "send_request_receipt_notification",
        "send_request_review_notification",
        "notification_service_type",
        "enable_property_specific_messaging",
    ],
    "security": [
        "cors_origins",
        "cors_origin_regex",
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
    "consent": ["override_vendor_purposes"],
    "admin_ui": ["enabled", "url"],
}
