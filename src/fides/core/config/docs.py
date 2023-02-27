"""
This module auto-generates a documented config from the config source.
"""
import os
from textwrap import wrap
from typing import Dict, List, Set

import toml
from click import echo
from pydantic import BaseSettings

from fides.core.config import FidesConfig, get_config

CONFIG_DOCS_URL = "https://ethyca.github.io/fides/stable/config/"
HELP_LINK = f"# For more info, please visit: {CONFIG_DOCS_URL}\n"


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
        for settings_name, settings_info in config.schema()["properties"].items()
        if not settings_info.get("type")
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
    elif value_type == "boolean":
        return str(value).lower()
    elif value_type == "array":
        return "[]"
    return value


def build_field_documentation(field_name: str, field_info: Dict[str, str]) -> str:
    """Build a docstring for an individual docstring."""
    try:
        field_type = field_info["type"]
        field_description = "\n".join(
            wrap(
                text=field_info["description"],
                width=71,
                subsequent_indent="# ",
                initial_indent="# ",
            )
        )
        field_default = format_value_for_toml(field_info.get("default", ""), field_type)
        doc_string = (
            f"{field_description}\n{field_name} = {field_default} # {field_type}\n"
        )
        return doc_string
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
    settings_docstring = f"[{object_name}] # {settings_description}\n" + HELP_LINK

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
    included_keys = set(settings.dict().keys())
    title_header = build_section_header(settings_name)

    # Build the Section docstring
    settings_description = settings_schema["description"]
    settings_docstring = f"[{settings_name}] # {settings_description}\n"

    # Build the field docstrings
    fields = remove_excluded_fields(settings_schema["properties"], included_keys)
    field_docstrings = [
        build_field_documentation(field_name, field_info)
        for field_name, field_info in fields.items()
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
    docs: str = "\n".join(nested_settings_docs + object_docs)

    # Verify it is valid TOML before writing it out
    toml.loads(docs)

    if "# TODO" in docs:
        raise SystemExit(
            "All fields require documentation, no description TODOs allowed!"
        )

    with open(outfile_path, "w", encoding="utf-8") as output_file:
        output_file.write(docs)
        print(f"Exported configuration file to: {outfile_path}")

    # Verify it is a valid Fides config file
    get_config(outfile_path)


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
