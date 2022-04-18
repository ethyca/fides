"""Utils to help with API calls."""
import logging
from functools import partial
from json.decoder import JSONDecodeError
from typing import Dict, Iterator

import click
import jwt
import requests
import sqlalchemy
from sqlalchemy.engine import Engine

from fideslang.models import DatasetField

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


def jwt_encode(user_id: int, api_key: str) -> str:
    """
    Encode user information into server-required JWT token
    """
    return jwt.encode({"uid": user_id}, api_key, algorithm="HS256")


def generate_request_headers(user_id: str, api_key: str) -> Dict[str, str]:
    """
    Generate the headers for a request.
    """
    return {
        "Content-Type": "application/json",
        "user-id": str(user_id),
        "Authorization": "Bearer {}".format(jwt_encode(1, api_key)),
    }


def get_all_level_fields(fields: list) -> Iterator[DatasetField]:
    """
    Traverses all levels of fields that exist in a dataset
    returning them for individual evaluation.
    """
    for field in fields:
        yield field
        if field.fields:
            for nested_field in get_all_level_fields(field.fields):
                yield nested_field
