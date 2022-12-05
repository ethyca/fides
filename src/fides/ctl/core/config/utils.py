import logging
import os
from os import getenv
from pathlib import Path
from typing import Any, Dict, List, Union

from click import echo
from toml import dump, load

from fides.ctl.core.utils import echo_red

DEFAULT_CONFIG_PATH = ".fides/fides.toml"
logger = logging.getLogger(__name__)


def get_test_mode() -> bool:
    test_mode = getenv("FIDES__TEST_MODE", "").lower() == "true"
    return test_mode


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


def check_required_webserver_config_values() -> None:
    """Check for required env vars and print a user-friendly error message."""
    required_config_dict = {
        "app_encryption_key": {
            "env_var": "FIDES__SECURITY__APP_ENCRYPTION_KEY",
            "config_subsection": "security",
        },
        "oauth_root_client_id": {
            "env_var": "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID",
            "config_subsection": "security",
        },
        "oauth_root_client_secret": {
            "env_var": "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET",
            "config_subsection": "security",
        },
    }

    missing_required_config_vars = []
    for key, value in required_config_dict.items():
        try:
            config_value = getenv(value["env_var"]) or get_config_from_file(
                "",
                value["config_subsection"],
                key,
            )
        except FileNotFoundError:
            config_value = None

        if not config_value:
            missing_required_config_vars.append(key)

    if missing_required_config_vars:
        echo_red(
            "\nThere are missing required configuration variables. Please add the following config variables to either the "
            "`fides.toml` file or your environment variables to start Fides: \n"
        )
        for missing_value in missing_required_config_vars:
            print(f"- {missing_value}")
        print(
            "\nVisit the Fides deployment documentation for more information: "
            "https://ethyca.github.io/fides/deployment/"
        )

        raise SystemExit(1)
