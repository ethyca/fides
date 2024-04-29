"""
These utils are designed to be safe to use across Fides, with no potential for circular dependencies.

These utils should only import from 3rd-party libraries, with zero imports
from local Fides modules.
"""

import json
import pprint
import sys
from functools import partial
from json.decoder import JSONDecodeError
from typing import Dict, Union

import click
import requests
from loguru import logger

echo_red = partial(click.secho, fg="red", bold=True)
echo_green = partial(click.secho, fg="green", bold=True)


def print_divider(character: str = "-", character_length: int = 10) -> None:
    """
    Returns a consistent visual/textual divider to make terminal
    output more human-readable.
    """
    print(character * character_length)


def pretty_echo(dict_object: Union[Dict, str], color: str = "white") -> None:
    """
    Given a dict-like object and a color, pretty click echo it.
    """
    click.secho(pprint.pformat(dict_object, indent=2, width=80, compact=True), fg=color)


def handle_cli_response(
    response: requests.Response, verbose: bool = True
) -> requests.Response:
    """Viewable CLI response"""
    if response.status_code >= 200 and response.status_code <= 299:
        if verbose:
            pretty_echo(response.json(), "green")
    else:
        try:
            pretty_echo(response.json(), "red")
        except json.JSONDecodeError:
            click.secho(response.text, fg="red")
        finally:
            sys.exit(1)
    return response


def check_response_auth(response: requests.Response) -> requests.Response:
    """
    Verify that a response object is 'ok', otherwise print the error and raise
    an exception.
    """
    if response.status_code in [401, 403]:
        echo_red("Authorization Error: please try 'fides user login' and try again.")
        raise SystemExit(1)
    return response


def check_response(response: requests.Response) -> requests.Response:
    """
    Check that a response has valid JSON.
    """

    try:
        response.json()
    except JSONDecodeError as json_error:
        logger.error(response.status_code)
        logger.error(response.text)
        raise json_error
    else:
        return response
