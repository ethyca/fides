from typing import Callable

import click

from fideslang import model_list


def object_type_argument(command: Callable) -> Callable:
    """
    Apply the object_type option.
    """
    command = click.argument(
        "object_type", type=click.Choice(model_list, case_sensitive=False)
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
