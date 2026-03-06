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
from hashlib import sha1
from json.decoder import JSONDecodeError
from typing import Any, Dict, Iterator, Union

import click
import requests
import sqlalchemy
from fideslang.models import DatasetField
from loguru import logger
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


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


FIDES_ASCII_ART = """

███████╗██╗██████╗ ███████╗███████╗
██╔════╝██║██╔══██╗██╔════╝██╔════╝
█████╗  ██║██║  ██║█████╗  ███████╗
██╔══╝  ██║██║  ██║██╔══╝  ╚════██║
██║     ██║██████╔╝███████╗███████║
╚═╝     ╚═╝╚═════╝ ╚══════╝╚══════╝
"""


# ---------------------------------------------------------------------------
# Extracted from core/utils.py -- used by non-CLI code across both repos
# ---------------------------------------------------------------------------


def sanitize_fides_key(proposed_fides_key: str) -> str:
    """
    Attempts to manually sanitize a fides key if restricted
    characters are discovered.
    """
    sanitized_fides_key = re.sub(r"[^a-zA-Z0-9_.-]", "_", proposed_fides_key)
    return sanitized_fides_key


def generate_unique_fides_key(
    proposed_fides_key: str, database_host: str, database_name: str
) -> str:
    """
    Uses host and name to generate a UUID to be
    appended to the fides_key of a dataset.
    """
    fides_key_uuid = sha1(
        "-".join([database_host, database_name, proposed_fides_key]).encode()
    )
    return f"{proposed_fides_key}_{fides_key_uuid.hexdigest()[:10]}"


def get_all_level_fields(fields: list) -> Iterator[DatasetField]:
    """
    Traverses all levels of fields that exist in a dataset
    returning them for individual evaluation.
    """
    for field in fields:
        yield field
        if isinstance(field, dict):
            if field["fields"]:
                yield from get_all_level_fields(field["fields"])
        else:
            if field.fields:
                yield from get_all_level_fields(field.fields)


def get_db_engine(connection_string: str) -> Engine:
    """
    Use SQLAlchemy to create a DB engine.
    """
    connect_args: Dict[str, Any] = (
        {"connect_timeout": 10} if "pymssql" not in connection_string else {}
    )
    if "redshift" in connection_string:
        connect_args["sslmode"] = "prefer"
        connect_args["connect_timeout"] = 60
    try:
        engine = sqlalchemy.create_engine(connection_string, connect_args=connect_args)
    except Exception as err:
        raise Exception("Failed to create engine!") from err

    try:
        with engine.begin() as connection:
            connection.execute("SELECT 1")
    except Exception as err:
        raise Exception(f"Database connection failed with engine:\n{engine}!") from err
    return engine


def validate_db_engine(connection_string: str) -> None:
    """
    Validate that a database connection string can successfully connect.

    Raises SQLAlchemyError on failure.
    """
    connect_args: Dict[str, Any] = (
        {"connect_timeout": 10} if "pymssql" not in connection_string else {}
    )
    if "redshift" in connection_string:
        connect_args["sslmode"] = "prefer"
        connect_args["connect_timeout"] = 60
    try:
        engine = sqlalchemy.create_engine(connection_string, connect_args=connect_args)
        with engine.begin() as connection:
            connection.execute("SELECT 1")
    except SQLAlchemyError:
        raise
