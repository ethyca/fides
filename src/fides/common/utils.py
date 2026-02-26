"""
These utils are designed to be safe to use across Fides, with no potential for circular dependencies.

These utils should only import from 3rd-party libraries, with zero imports
from local Fides modules.
"""

import json
import pprint
import re
import sys
from functools import partial
from json.decoder import JSONDecodeError
from typing import Dict, Union

import click
import requests
from loguru import logger


def clean_version(version: str) -> str:
    """
    Clean up version strings for user display.

    Removes:
    - The dirty suffix (.dirty or -dirty) added when there are uncommitted changes
    - The +0.gXXXXXX suffix when exactly on a tag (zero commits past)

    Examples:
        2.99.0 -> 2.99.0 (unchanged)
        2.78.0a1 -> 2.78.0a1 (unchanged)
        2.78.1a0+0.gabcdef -> 2.78.1a0 (strip zero-distance suffix)
        2.78.1a0+0.gabcdef.dirty -> 2.78.1a0 (strip both)
        2.78.0a1+5.gabcdef -> 2.78.0a1+5.gabcdef (keep non-zero distance)
        2.78.0a1+5.gabcdef.dirty -> 2.78.0a1+5.gabcdef (strip dirty only)
    """
    # First remove dirty suffix
    version = re.sub(r"[.-]dirty$", "", version)
    # Then remove +0.gXXXXXX suffix (zero commits past tag)
    version = re.sub(r"\+0\.g[a-f0-9]+$", "", version)
    return version


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

    return response
