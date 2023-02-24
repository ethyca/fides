"""
This module handles generating documentation from code.
"""
import toml
from typing import Dict, Any, Set, List
import json
import sys

from fides.api.main import app
from fides.core.config import CONFIG, FidesConfig, get_config
from pydantic import BaseSettings


def get_non_object_fields(schema_properties: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Get the list of fields from the schema that are not references
    to other settings objects.

    Nested Pydantic settings objects don't have the `type` key, and generic
    objects like dictionaries have the `object` type.
    """
    non_object_fields = {
        field_name: field_info
        for field_name, field_info in schema_properties.items()
        if field_info.get("type") and field_info.get("type") != "object"
    }
    return non_object_fields


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
        if not settings_info.get("type") and settings_info.get("type") != "object"
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
    else:
        return value


def build_field_documentation(field_name: str, field_info: Dict[str, str]) -> str:
    """Build a docstring for an individual docstring."""
    try:
        field_type = field_info["type"]
        field_description = field_info["description"]
        field_default = format_value_for_toml(field_info.get("default", ""), field_type)
        doc_string = (
            f"# {field_description}\n{field_name} = {field_default} # {field_type}\n"
        )
        return doc_string
    except KeyError:
        print(field_info)
        raise SystemExit(f"!Failed to parse field: {field_name}!")


def join_section_field_docstrings(
    settings_docstring: str, field_docstrings: List[str]
) -> str:
    """Joins a section docstring with a list of docstrings by field."""
    joined_docstrings = settings_docstring + "\n" + "\n".join(field_docstrings)
    return joined_docstrings


def convert_settings_to_toml_docs(settings_name: str, settings: BaseSettings) -> str:
    """
    Takes a Pydantic settings object and returns a
    formatted string with included metadata.

    The string is expected to be valid TOML.
    """
    settings_schema = settings.schema()
    included_keys = set(settings.dict().keys())

    print(f"> Building docs for section: {settings_name}...")
    # Build the Section docstring
    settings_description = settings_schema["description"]
    settings_docstring = f"[{settings_name}] # {settings_description}\n"

    # Build the field docstrings
    fields = remove_excluded_fields(settings_schema["properties"], included_keys)
    field_docstrings = [
        build_field_documentation(field_name, field_info)
        for field_name, field_info in fields.items()
    ]

    joined_docstrings = join_section_field_docstrings(
        settings_docstring, field_docstrings
    )
    print(f"{settings_name} docs built successfully.")
    return joined_docstrings


def remove_excluded_fields(
    fields: Dict[str, Dict], included_fields: Set[str]
) -> Dict[str, Dict]:
    """Remove fields that are marked as 'excluded=True' in their field."""
    without_excluded_fields = {
        key: value for key, value in fields.items() if key in included_fields
    }
    return without_excluded_fields


def get_toplevel_docs(config: FidesConfig) -> str:
    """Generate the doc for the top-level of the configuration file."""
    included_keys = set(config.dict().keys())
    schema = config.schema()

    config_description = "# Default Configuration File for Fides\n"
    toplevel_fields: Dict[str, Dict] = get_non_object_fields(schema["properties"])
    included_toplevel_fields: Dict[str, Dict] = remove_excluded_fields(
        toplevel_fields, included_keys
    )
    toplevel_field_docstrings: List[str] = [
        build_field_documentation(field_name, field_info)
        for field_name, field_info in included_toplevel_fields.items()
    ]
    toplevel_docstring: str = join_section_field_docstrings(
        config_description, toplevel_field_docstrings
    )
    return toplevel_docstring


def generate_config_docs(outfile_dir: str) -> None:
    """
    Autogenerate the schema for the configuration file
    and format it nicely for HTML.
    """

    outfile_name = "config/config_docs.toml"
    outfile_path = f"{outfile_dir}/{outfile_name}"

    print("> Building toplevel docs...")
    toplevel_docs = get_toplevel_docs(CONFIG)
    print("Toplevel docs built successfully.")

    # Build docstrings for the nested settings
    nested_settings: Dict[str, BaseSettings] = get_nested_settings(CONFIG)
    nested_settings_docs: List[str] = [
        convert_settings_to_toml_docs(settings_name, settings_schema)
        for settings_name, settings_schema in nested_settings.items()
    ]
    nested_settings_docs: str = "\n".join(nested_settings_docs)

    # Combine the docstrings
    docs_list = [toplevel_docs, nested_settings_docs]
    docs = "\n".join(docs_list)

    # Verify it is valid TOML before writing it out
    toml.loads(docs)

    with open(outfile_path, "w") as output_file:
        output_file.write(docs)
        print(f"Exported configuration schema to: {outfile_path}")

    # Verify it is a valid Fides config file
    get_config(outfile_path)

def generate_openapi(outfile_dir: str) -> str:
    "Write out an openapi.json file for the API."

    outfile_name = "api/openapi.json"
    outfile_path = f"{outfile_dir}/{outfile_name}"
    print(f"Generating OpenAPI JSON from the API and writing to '{outfile_path}'...")
    with open(outfile_path, "w") as outfile:
        json.dump(app.openapi(), outfile, indent=2)
        print(f"Exported OpenAPI JSON from the API to '{outfile_path}'")
    return outfile_path


if __name__ == "__main__":
    default_outfile_dir = "docs/fides/docs"
    try:
        outfile_dir = sys.argv[1]
    except IndexError:
        outfile_dir = default_outfile_dir

    generate_openapi(outfile_dir)
    generate_config_docs(outfile_dir)
