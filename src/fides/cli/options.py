"""
Contains all of the options/arguments used by the CLI commands.
"""

from typing import Callable

import click
from fideslang import model_list


def coverage_threshold_option(command: Callable) -> Callable:
    "Add a flag that assumes yes."
    command = click.option(
        "--coverage-threshold", "-c", type=click.IntRange(0, 100), default=100
    )(command)
    return command


def resource_type_argument(command: Callable) -> Callable:
    "Add the resource_type option."
    command = click.argument(
        "resource_type",
        type=click.Choice(model_list, case_sensitive=False),
    )(command)
    return command


def fides_key_argument(command: Callable) -> Callable:
    "Add the fides_key argument."
    command = click.argument(
        "fides_key",
        type=str,
    )(command)
    return command


def fides_key_option(command: Callable) -> Callable:
    "Add the fides_key option."
    command = click.option(
        "-k",
        "--fides-key",
        default="",
        help="The fides_key of the single policy that you wish to evaluate.",
    )(command)
    return command


def manifests_dir_argument(command: Callable) -> Callable:
    "Add the manifests_dir argument."
    command = click.argument(
        "manifests_dir",
        default=".fides/",
        type=click.Path(exists=True),
    )(command)
    return command


def dry_flag(command: Callable) -> Callable:
    "Add a flag that prevents side-effects."
    command = click.option(
        "--dry", is_flag=True, help="Prevent the persistance of any changes."
    )(command)
    return command


def yes_flag(command: Callable) -> Callable:
    "Add a flag that assumes yes."
    command = click.option(
        "--yes",
        "-y",
        is_flag=True,
        help="Automatically responds 'yes' to any prompts.",
    )(command)
    return command


def verbose_flag(command: Callable) -> Callable:
    "Turns on verbose output."
    command = click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose output.",
    )(command)
    return command


def include_null_flag(command: Callable) -> Callable:
    "Include null attributes in resource output."
    command = click.option(
        "--include-null",
        is_flag=True,
        help="Includes attributes that would otherwise be null.",
    )(command)
    return command


def organization_fides_key_option(command: Callable) -> Callable:
    "Add the organization_fides_key option."
    command = click.option(
        "--org-key",
        "-k",
        default="default_organization",
        help="The organization_fides_key you wish to export resources for.",
    )(command)
    return command


def output_directory_option(command: Callable) -> Callable:
    "Add the output directory option"
    command = click.option(
        "--output-dir",
        "-d",
        default=".fides/",
        help="The output directory for the data map to be exported to.",
    )(command)
    return command


def credentials_id_option(command: Callable) -> Callable:
    "Use credentials defined within fides config."
    command = click.option(
        "--credentials-id",
        type=str,
        help="Use credentials defined within fides config",
    )(command)
    return command


def connection_string_option(command: Callable) -> Callable:
    "Use connection string option to connect to a database"
    command = click.option(
        "--connection-string",
        type=str,
        help="Use connection string option to connect to a database",
    )(command)
    return command


def okta_org_url_option(command: Callable) -> Callable:
    "Use org url option to connect to okta. Requires options --org-url and --token"
    command = click.option(
        "--org-url",
        type=str,
        help="Use org url option to connect to okta. Requires options --org-url and --token",
    )(command)
    return command


def okta_token_option(command: Callable) -> Callable:
    "Use token option to connect to okta. Requires options --org-url and --token"
    command = click.option(
        "--token",
        type=str,
        help="Use token option to connect to okta. Requires options --org-url and --token",
    )(command)
    return command


def aws_access_key_id_option(command: Callable) -> Callable:
    "Use access key id option to connect to aws. Requires options --access_key_id, access_key and --region"
    command = click.option(
        "--access_key_id",
        type=str,
        help="Use access key id option to connect to aws. Requires options --access_key_id, --secret_access_key and --region",
    )(command)
    return command


def aws_secret_access_key_option(command: Callable) -> Callable:
    "Use access key option to connect to aws. Requires options --access_key_id, --secret_access_key and --region"
    command = click.option(
        "--secret_access_key",
        type=str,
        help="Use access key option to connect to aws. Requires options --access_key_id, --secret_access_key and --region",
    )(command)
    return command


def aws_region_option(command: Callable) -> Callable:
    "Use region option to connect to aws. Requires options --access_key_id, access_key and --region"
    command = click.option(
        "--region",
        type=str,
        help="Use region option to connect to aws. Requires options --access_key_id, --secret_access_key and --region",
    )(command)
    return command
