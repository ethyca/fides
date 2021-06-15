"""Utils to help with API calls."""
import logging
from functools import partial
from json.decoder import JSONDecodeError

import click
import requests
import sqlalchemy
from sqlalchemy.engine import Engine

from fidesctl.core import models

logger = logging.getLogger("server_api")

echo_red = partial(click.secho, fg="red", bold=True)
echo_green = partial(click.secho, fg="green", bold=True)


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


def get_db_engine(connection_string: str) -> Engine:
    """
    Use SQLAlchemy to create a DB engine.
    """
    try:
        engine = sqlalchemy.create_engine(connection_string)
    except Exception as err:
        echo_red("Failed to create engine!")
        raise SystemExit(err)

    try:
        with engine.begin() as connection:
            connection.execute("SELECT 1")
    except Exception as err:
        echo_red(f"Database connection failed with engine:\n{engine}!")
        raise SystemExit(err)
    return engine
