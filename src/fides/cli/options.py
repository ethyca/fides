"""
Reusable command-line arguments and options.
"""

from typing import Callable

import rich_click as click
from fideslang import model_list

# Note - the type: ignore comments throughout this file are a workaround
# for a known issue with the `click` library:
# https://github.com/pallets/click/issues/2558
# If/when that issue is resolved, they can be removed.


def diff_flag(command: Callable) -> Callable:
    """Print any diffs between the local & server objects"""
    command = click.option(
        "--diff",
        is_flag=True,
        help="Print any diffs between the local & server objects",
    )(
        command
    )  # type: ignore
    return command


def coverage_threshold_option(command: Callable) -> Callable:
    """An option decorator that sets a required coverage percentage."""
    command = click.option(
        "--coverage-threshold",
        "-c",
        type=click.IntRange(0, 100),
        default=100,
        help="Set the coverage percentage for a passing scan.",
    )(
        command
    )  # type: ignore
    return command


def resource_type_argument(command: Callable) -> Callable:
    "Add the resource_type argument."
    command = click.argument(
        "resource_type",
        type=click.Choice(model_list, case_sensitive=False),
    )(
        command
    )  # type: ignore
    return command


def resource_type_option(command: Callable) -> Callable:
    "Add the resource_type option."
    command = click.option(
        "--resource-type",
        default="",
        help=f"Choose from {str(model_list)}",
    )(
        command
    )  # type: ignore
    return command


def fides_key_argument(command: Callable) -> Callable:
    "Add the fides_key argument."
    command = click.argument(
        "fides_key",
        type=str,
    )(
        command
    )  # type: ignore
    return command


def fides_key_option(command: Callable) -> Callable:
    "Add the fides_key option."
    command = click.option(
        "-k",
        "--fides-key",
        default="",
    )(
        command
    )  # type: ignore
    return command


def manifests_dir_argument(command: Callable) -> Callable:
    "Add the manifests_dir argument."
    command = click.argument(
        "manifests_dir", type=click.Path(exists=True), default=".fides/"
    )(
        command
    )  # type: ignore
    return command


def dry_flag(command: Callable) -> Callable:
    "Add a flag that prevents side-effects."
    command = click.option(
        "--dry", is_flag=True, help="Do not upload results to the Fides webserver."
    )(
        command
    )  # type: ignore
    return command


def yes_flag(command: Callable) -> Callable:
    "Add a flag that assumes yes."
    command = click.option(
        "--yes",
        "-y",
        is_flag=True,
        help="Automatically responds `yes` to any prompts.",
    )(
        command
    )  # type: ignore
    return command


def verbose_flag(command: Callable) -> Callable:
    "Turns on verbose output."
    command = click.option(
        "--verbose",
        "-v",
        is_flag=True,
        help="Enable verbose output.",
    )(
        command
    )  # type: ignore
    return command


def include_null_flag(command: Callable) -> Callable:
    "Include null attributes in resource output."
    command = click.option(
        "--include-null",
        is_flag=True,
        help="Include null attributes.",
    )(
        command
    )  # type: ignore
    return command


def organization_fides_key_option(command: Callable) -> Callable:
    "Add the organization_fides_key option."
    command = click.option(
        "--org-key",
        "-k",
        default="default_organization",
        show_default=True,
        help="The `organization_fides_key` of the `Organization` you want to specify.",
    )(
        command
    )  # type: ignore
    return command


def output_directory_option(command: Callable) -> Callable:
    "Add the output directory option"
    command = click.option(
        "--output-dir",
        "-d",
        default=".fides/",
        show_default=True,
        help="The output directory for the data map to be exported to.",
    )(
        command
    )  # type: ignore
    return command


def credentials_id_option(command: Callable) -> Callable:
    "Use credentials defined within fides config."
    command = click.option(
        "--credentials-id",
        type=str,
        help="Use credentials keys defined within Fides config.",
    )(
        command
    )  # type: ignore
    return command


def connection_string_option(command: Callable) -> Callable:
    "Use connection string option to connect to a database"
    command = click.option(
        "--connection-string",
        type=str,
        help="Use the connection string option to connect to a database.",
    )(
        command
    )  # type: ignore
    return command


def okta_org_url_option(command: Callable) -> Callable:
    "Use org url option to connect to okta. Requires options --org-url and --token"
    command = click.option(
        "--org-url",
        type=str,
        help="Connect to Okta using an 'Org URL'. _Requires options `--org-url` & `--token`._",
    )(
        command
    )  # type: ignore
    return command


def okta_token_option(command: Callable) -> Callable:
    "Use token option to connect to okta. Requires options --org-url and --token"
    command = click.option(
        "--token",
        type=str,
        help="Connect to Okta using a token. _Requires options `--org-url` and `--token`._",
    )(
        command
    )  # type: ignore
    return command


def aws_access_key_id_option(command: Callable) -> Callable:
    "Use access key id option to connect to aws. Requires options --access_key_id, access_key and --region"
    command = click.option(
        "--access_key_id",
        type=str,
        help="Connect to AWS using an `Access Key ID`. _Requires options `--access_key_id`, `--secret_access_key` & `--region`._",
    )(
        command
    )  # type: ignore
    return command


def aws_secret_access_key_option(command: Callable) -> Callable:
    "Use access key option to connect to aws. Requires options --access_key_id, --secret_access_key and --region"
    command = click.option(
        "--secret_access_key",
        type=str,
        help="Connect to AWS using an `Access Key`. _Requires options `--access_key_id`, `--secret_access_key` & `--region`._",
    )(
        command
    )  # type: ignore
    return command


def aws_session_token_option(command: Callable) -> Callable:
    "Use a session token with temporary access keys to connect to aws. Requires options --access_key_id, --secret_access_key and --region"
    command = click.option(
        "--session_token",
        type=str,
        default="",
        help="Connect to AWS using a temporary `Access Key`. _Requires options `--access_key_id`, `--secret_access_key`, `--session_token`, & `--region`._",
    )(
        command
    )  # type: ignore
    return command


def aws_region_option(command: Callable) -> Callable:
    "Use region option to connect to aws. Requires options --access_key_id, access_key and --region"
    command = click.option(
        "--region",
        type=str,
        help="Connect to AWS using a specific `Region`. _Requires options `--access_key_id`, `--secret_access_key` & `--region`._",
    )(
        command
    )  # type: ignore
    return command


def prompt_username(ctx: click.Context, param: str, value: str) -> str:
    """Check the config for a compatible username. If unavailable, prompt the user to provide one."""
    config_value = ctx.obj["CONFIG"].user.username

    if value:
        return value

    if config_value:
        click.echo("> Username found in configuration.")
        return config_value

    value = click.prompt(text="Username")  # pragma: no cover
    return value


def prompt_password(ctx: click.Context, param: str, value: str) -> str:
    """Check the config for a compatible password. If unavailable, prompt the user to provide one."""
    config_value = ctx.obj["CONFIG"].user.password

    if value:
        return value

    if config_value:
        click.echo("> Password found in configuration.")
        return config_value

    value = click.prompt(text="Password", hide_input=True)  # pragma: no cover
    return value


def username_option(command: Callable) -> Callable:
    command = click.option(
        "-u",
        "--username",
        help="If not provided, will be pulled from the config file or prompted for.",
        default="",
        callback=prompt_username,
    )(
        command
    )  # type: ignore
    return command


def password_option(command: Callable) -> Callable:
    command = click.option(
        "-p",
        "--password",
        help="If not provided, will be pulled from the config file or prompted for.",
        default="",
        callback=prompt_password,
    )(
        command
    )  # type: ignore
    return command


def first_name_option(command: Callable) -> Callable:
    command = click.option(
        "-f",
        "--first-name",
        default="",
    )(
        command
    )  # type: ignore
    return command


def last_name_option(command: Callable) -> Callable:
    command = click.option(
        "-l",
        "--last-name",
        default="",
    )(
        command
    )  # type: ignore
    return command


def username_argument(command: Callable) -> Callable:
    command = click.argument("username", type=str)(command)  # type: ignore
    return command


def password_argument(command: Callable) -> Callable:
    command = click.argument("password", type=str)(command)  # type: ignore
    return command


def email_address_argument(command: Callable) -> Callable:
    command = click.argument("email_address", type=str)(command)  # type: ignore
    return command
