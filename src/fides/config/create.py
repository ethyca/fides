"""
This module auto-generates a documented config from the config source.
"""

import os
from textwrap import wrap
from typing import Dict, List, Optional, Set, Tuple

import toml
from click import echo
from pydantic_settings import BaseSettings

from fides.cli.utils import request_analytics_consent
from fides.config import FidesConfig, build_config
from fides.config.utils import replace_config_value

CONFIG_DOCS_URL = "https://ethyca.github.io/fides/stable/config/"
HELP_LINK = f"# For more info, please visit: {CONFIG_DOCS_URL}"


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
                    # Getting first non-null
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

    # Build the Section docstring
    settings_description = object_info["description"]
    settings_docstring = (
        f"[{object_name}] # {settings_description}\n{HELP_LINK}#{object_name}\n"
    )

    # Build the field docstrings
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

    # Build the Section docstring
    settings_description = settings_schema["description"]
    settings_docstring = f"[{settings_name}] # {settings_description}\n"

    # Build the field docstrings
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

    # Create the docs for the special "object" fields
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

    # Create the docs for the nested settings objects
    settings: Dict[str, BaseSettings] = get_nested_settings(config)
    ordered_settings: Dict[str, BaseSettings] = {
        name: settings[name] for name in sorted(set(settings.keys()))
    }
    nested_settings_docs: List[str] = [
        convert_settings_to_toml_docs(settings_name, settings_schema)
        for settings_name, settings_schema in ordered_settings.items()
    ]

    # Combine all of the docs
    docs: str = build_config_header() + "\n".join(nested_settings_docs + object_docs)

    # Verify it is a valid Fides config file
    validate_generated_config(docs)

    with open(outfile_path, "w", encoding="utf-8") as output_file:
        output_file.write(docs)
        print(f"Exported configuration file to: {outfile_path}")


def create_config_file(config: FidesConfig, fides_directory_location: str = ".") -> str:
    """
    Initializes the .fides/fides.toml file if it doesn't exist.

    Returns the config_path if successful.
    """
    fides_dir_name = ".fides"
    fides_dir_path = f"{fides_directory_location}/{fides_dir_name}"
    config_file_name = "fides.toml"
    config_path = f"{fides_dir_path}/{config_file_name}"

    # create the .fides dir if it doesn't exist
    if not os.path.exists(fides_dir_path):
        os.mkdir(fides_dir_path)
        echo(f"Created a '{fides_dir_path}' directory.")
    else:
        echo(f"Directory '{fides_dir_path}' already exists.")

    # create a fides.toml config file if it doesn't exist
    if not os.path.isfile(config_path):
        generate_config_docs(config, config_path)
    else:
        echo(f"Configuration file already exists: {config_path}")

    echo("To learn more about configuring fides, see:")
    echo("\thttps://ethyca.github.io/fides/config/")

    return config_path


def create_and_update_config_file(
    config: FidesConfig,
    fides_directory_location: str = ".",
    opt_in: bool = False,
) -> Tuple[FidesConfig, str]:
    # request explicit consent for analytics collection
    config = request_analytics_consent(config=config, opt_in=opt_in)

    # create the config file as needed
    config_path = create_config_file(
        config=config, fides_directory_location=fides_directory_location
    )

    # Update the value in the config file if it differs from the default
    if not config.user.analytics_opt_out:
        replace_config_value(
            fides_directory_location=fides_directory_location,
            key="analytics_opt_out",
            old_value="true",
            new_value="false",
        )
    return (config, config_path)
