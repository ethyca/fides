from typing import Callable

import click

from fidesctl.core.models import MODEL_LIST


def object_type_argument(command: Callable) -> Callable:
    """
    Apply the object_type option.
    """
    command = click.argument(
        "object_type", type=click.Choice(MODEL_LIST, case_sensitive=False)
    )(command)
    return command


def manifest_option(command: Callable) -> Callable:
    """
    Apply the manifest option.
    """
    command = click.option(
        "--manifest",
        "-m",
        "manifest",
        required=True,
        type=click.Path(exists=True),
        help="Path to the manifest file",
    )(command)
    return command


def id_argument(command: Callable) -> Callable:
    """
    Apply the id argument.
    """
    command = click.argument(
        "object_id",
        type=str,
    )(command)
    return command
