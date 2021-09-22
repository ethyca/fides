"""
Contains all of the options/arguments used by the CLI commands.
"""

from typing import Callable

import click

from fideslang import model_list


def resource_type_argument(command: Callable) -> Callable:
    "Add the resource_type option."
    command = click.argument(
        "resource_type", type=click.Choice(model_list, case_sensitive=False)
    )(command)
    return command


def fides_key_argument(command: Callable) -> Callable:
    "Add the id argument."
    command = click.argument(
        "fides_key",
        type=str,
    )(command)
    return command


def manifests_dir_argument(command: Callable) -> Callable:
    "Add the id argument."
    command = click.argument(
        "manifests_dir",
        type=click.Path(),
    )(command)
    return command


def dry_flag(command: Callable) -> Callable:
    "Add a flag that prevents side-effects."
    command = click.option(
        "--dry",
        is_flag=True,
        help="Runs the command without any side-effects.",
    )(command)
    return command
