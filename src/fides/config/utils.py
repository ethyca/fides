import os
from os import environ, getenv
from pathlib import Path
from re import compile as regex
from textwrap import wrap
from typing import Any, Dict, List, Optional, Set, Union

import toml
from click import echo
from pydantic_settings import BaseSettings
from toml import dump, load

from fides.config import FidesConfig

DEFAULT_CONFIG_PATH = ".fides/fides.toml"
DEFAULT_CONFIG_PATH_ENV_VAR = "FIDES__CONFIG_PATH"

CONFIG_DOCS_URL = "https://ethyca.github.io/fides/stable/config/"
HELP_LINK = f"# For more info, please visit: {CONFIG_DOCS_URL}"


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


def load_file(file_names: Union[List[Path], List[str]]) -> str:
    """
    Load a file from the first matching location.

    In order, will check:
    - A path set at ENV variable FIDES__CONFIG_PATH
    - The current directory
    - The parent directory
    - Two directories up for the current directory
    - The parent_directory/.fides
    - users home (~) directory
    raises FileNotFound if none is found
    """

    possible_directories = [
        os.getenv("FIDES__CONFIG_PATH"),
        os.curdir,
        os.pardir,
        os.path.abspath(os.path.join(os.curdir, "..", "..")),
        os.path.join(os.pardir, ".fides"),
        os.path.expanduser("~"),
    ]

    directories = [d for d in possible_directories if d]

    for dir_str in directories:
        for file_name in file_names:
            possible_location = os.path.join(dir_str, file_name)
            if possible_location and os.path.isfile(possible_location):
                return possible_location

    raise FileNotFoundError


def get_config_from_file(
    config_path_override: str,
    section: str,
    option: str,
) -> Union[str, bool, int, None]:
    """
    Return the value currently written to the config file for the
    specified `section.option`.
    """

    config_path = config_path_override or load_file(file_names=[DEFAULT_CONFIG_PATH])
    current_config = load(config_path)

    config_section = current_config.get(section)
    if config_section is not None:
        config_option = config_section.get(option)
        if config_option is not None:
            return config_option

    return None


def update_config_file(  # type: ignore
    updates: Dict[str, Dict[str, Any]],
    config_path_override: str,
) -> None:
    """
    Overwrite the existing config file with a new version that includes the desired `updates`.

    :param updates: A nested `dict`, where top-level keys correspond to configuration sections and top-level values contain `dict`s whose key/value pairs correspond to the desired option/value updates.
    :param config_path: The path to the current configuration file.
    """

    config_path = config_path_override or load_file(file_names=[DEFAULT_CONFIG_PATH])
    current_config = load(config_path)

    for key, value in updates.items():
        if key in current_config:
            current_config[key].update(value)
        else:
            current_config.update({key: value})

    with open(config_path, "w", encoding="utf-8") as config_file:
        dump(current_config, config_file)

    echo(f"Updated {config_path}:")

    for key, value in updates.items():
        for subkey, val in value.items():
            echo(f"\tSet {key}.{subkey} = {val}")


def handle_deprecated_fields(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Custom logic for handling deprecated values."""

    if settings.get("api") and not settings.get("database"):
        api_settings = settings.pop("api")
        database_settings = {}
        database_settings["user"] = api_settings.get("database_user")
        database_settings["password"] = api_settings.get("database_password")
        database_settings["server"] = api_settings.get("database_host")
        database_settings["port"] = api_settings.get("database_port")
        database_settings["db"] = api_settings.get("database_name")
        database_settings["test_db"] = api_settings.get("test_database_name")
        settings["database"] = database_settings

    return settings


def handle_deprecated_env_variables(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom logic for handling deprecated ENV variable configuration.
    """

    deprecated_env_vars = regex(r"FIDES__API__(\w+)")

    for key, val in environ.items():
        match = deprecated_env_vars.search(key)
        if match:
            setting = match.group(1).lower()
            setting = setting[setting.startswith("database_") and len("database_") :]
            if setting == "host":
                setting = "server"
            if setting == "name":
                setting = "db"
            if setting == "test_database_name":
                setting = "test_db"

            settings["database"][setting] = val

    return settings


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
        "memory_watchdog_enabled",
        "sql_dry_run",
    ],
    "storage": [
        "active_default_storage_type",
    ],
    "consent": ["override_vendor_purposes"],
    "admin_ui": ["enabled", "url", "error_notification_mode"],
    "privacy_center": ["url"],
    "privacy_request_duplicate_detection": [
        "enabled",
        "time_window_days",
        "match_identity_fields",
    ],
}


# ---------------------------------------------------------------------------
# Config doc generation -- auto-generates documented TOML from config schema
# ---------------------------------------------------------------------------


def get_nested_settings(config: FidesConfig) -> Dict[str, BaseSettings]:
    """
    Get the list of fields from the full configuration settings that refer to
    other settings objects.

    The filter here is a reversal of `get_non_object_fields` with
    some additional complexity added around getting the name of the class
    that gets used later.

    The returned object contains the name of the settings field as the key,
    with the value being the Pydantic settings class itself.
    """
    nested_settings = {
        settings_name
        for settings_name, settings_info in config.model_json_schema()[
            "properties"
        ].items()
        if not settings_info.get("type") and not settings_info.get("anyOf")
    }

    nested_settings_objects = {
        settings_name: getattr(config, settings_name)
        for settings_name in nested_settings
    }
    return nested_settings_objects


def format_value_for_toml(value: str, value_type: str) -> str:
    """Format the value into valid TOML."""
    if value_type == "string":
        return f'"{value}"'
    if value_type == "boolean":
        return str(value).lower()
    if value_type == "array":
        return "[]"
    return value


def build_field_documentation(field_name: str, field_info: Dict) -> Optional[str]:
    """Build a docstring for an individual docstring.

    This is error prone - this is attempts to pull data out of the Pydantic schema, but
    not every case is handled.
    """
    try:
        # Singular field types under "type"
        field_type: str = field_info.get("type") or ""
        if not field_type:
            # Union field types are under "anyOf"
            any_of: List[Dict[str, str]] = field_info.get("anyOf") or []
            for type_annotation in any_of:
                if type_annotation["type"] != "null":
                    field_type = type_annotation["type"]
                    break

        field_description: str = "\n".join(
            wrap(
                text=field_info.get("description") or "",
                width=71,
                subsequent_indent="# ",
                initial_indent="# ",
            )
        )
        field_default = field_info.get("default")
        if field_default is not None:
            formatted_default = format_value_for_toml(field_default, field_type)
            return f"{field_description}\n{field_name} = {formatted_default} # {field_type}\n"
        return None
    except KeyError:
        print(field_info)
        raise SystemExit(f"!Failed to parse field: {field_name}!")


def build_section_header(title: str) -> str:
    """Build a pretty, TOML-valid section header."""
    title_piece = f"#-- {title.upper()} --#\n"
    top_piece = f"#{'-' * (len(title_piece) - 3)}#\n"
    bottom_piece = f"#{'-' * 68}#\n"
    header = top_piece + title_piece + bottom_piece
    return header


def convert_object_to_toml_docs(object_name: str, object_info: Dict[str, str]) -> str:
    """
    Takes a Pydantic field of type `object` and returns a formatted string with included metadata.

    This is used to handle "special-case" top-level fields that aren't normal "settings" objects.
    """
    title_header = build_section_header(object_name)

    settings_description = object_info["description"]
    settings_docstring = (
        f"[{object_name}] # {settings_description}\n{HELP_LINK}#{object_name}\n"
    )

    full_docstring = title_header + settings_docstring
    return full_docstring


def convert_settings_to_toml_docs(settings_name: str, settings: BaseSettings) -> str:
    """
    Takes a Pydantic settings object and returns a
    formatted string with included metadata.

    The string is expected to be valid TOML.
    """
    settings_schema = settings.schema()
    included_keys = set(settings.model_dump(mode="json").keys())
    title_header = build_section_header(settings_name)

    settings_description = settings_schema["description"]
    settings_docstring = f"[{settings_name}] # {settings_description}\n"

    fields = remove_excluded_fields(settings_schema["properties"], included_keys)
    field_docstrings = [
        docstring
        for field_name, field_info in fields.items()
        if (docstring := build_field_documentation(field_name, field_info))
    ]
    full_docstring = (
        title_header + settings_docstring + "\n" + "\n".join(field_docstrings)
    )
    return full_docstring


def remove_excluded_fields(
    fields: Dict[str, Dict], included_fields: Set[str]
) -> Dict[str, Dict]:
    """Remove fields that are marked as 'excluded=True' in their field."""
    without_excluded_fields = {
        key: value for key, value in fields.items() if key in included_fields
    }
    return without_excluded_fields


def build_config_header() -> str:
    """Build the header to be used at the top of the config file."""
    config_header = f"# Fides Configuration File\n# Additional Documentation at : {CONFIG_DOCS_URL}\n\n"
    return config_header


def validate_generated_config(config_docs: str) -> None:
    """Run a few checks on the generated configuration docs."""
    from fides.config import build_config

    toml_docs = toml.loads(config_docs)
    build_config(toml_docs)
    if "# TODO" in config_docs:
        raise ValueError(
            "All fields require documentation, no description TODOs allowed!"
        )


def generate_config_docs(
    config: FidesConfig, outfile_path: str = ".fides/fides.toml"
) -> None:
    """
    Autogenerate the schema for the configuration file
    and format it nicely as valid TOML.

    _Any individual value at the top-level of the config is ignored!_
    """
    schema_properties: Dict[str, Dict] = config.schema()["properties"]
    object_fields = {
        settings_name: settings_info
        for settings_name, settings_info in schema_properties.items()
        if settings_info.get("type") == "object"
    }
    object_docs = [
        convert_object_to_toml_docs(object_name, object_info)
        for object_name, object_info in object_fields.items()
    ]

    settings: Dict[str, BaseSettings] = get_nested_settings(config)
    ordered_settings: Dict[str, BaseSettings] = {
        name: settings[name] for name in sorted(set(settings.keys()))
    }
    nested_settings_docs: List[str] = [
        convert_settings_to_toml_docs(settings_name, settings_schema)
        for settings_name, settings_schema in ordered_settings.items()
    ]

    docs: str = build_config_header() + "\n".join(nested_settings_docs + object_docs)

    validate_generated_config(docs)

    with open(outfile_path, "w", encoding="utf-8") as output_file:
        output_file.write(docs)
        print(f"Exported configuration file to: {outfile_path}")
