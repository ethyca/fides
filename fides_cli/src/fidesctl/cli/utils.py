"""Contains reusable utils for the CLI commands."""
import json
import os
from typing import Dict, Callable

import click
import requests

from fidesctl.core.models import MODEL_LIST


def pretty_echo(dict_object: Dict, color: str = "white") -> None:
    """
    Given a dict-like object and a color, pretty click echo it.
    """
    click.secho(json.dumps(dict_object, indent=2), fg=color)


def handle_cli_response(response: requests.Response) -> requests.Response:
    """Viewable CLI response"""
    if response.status_code == 200:
        pretty_echo(response.json(), "green")
    else:
        try:
            pretty_echo(response.json(), "red")
        except json.JSONDecodeError:
            click.secho(response.text, fg="red")
    return response


def url_option(command: Callable) -> Callable:
    """
    Apply the url option.
    """
    command = click.option(
        "--url",
        "-u",
        "url",
        default=lambda: os.getenv("FIDES_SERVER_URL", ""),
        help="URL of the Fides Server",
    )(command)
    return command


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
