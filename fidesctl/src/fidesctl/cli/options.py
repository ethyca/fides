from typing import Callable

import click

from fideslang import model_list


def object_type_argument(command: Callable) -> Callable:
    "Add the object_type option."
    command = click.argument(
        "object_type", type=click.Choice(model_list, case_sensitive=False)
    )(command)
    return command


def id_argument(command: Callable) -> Callable:
    "Add the id argument."
    command = click.argument(
        "object_id",
        type=str,
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
        "manifest_dir",
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
