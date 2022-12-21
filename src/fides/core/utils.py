"""Utils to help with API calls."""
import glob
import re
from functools import partial
from hashlib import sha1
from json.decoder import JSONDecodeError
from os.path import isfile
from typing import Dict, Iterator, List

import click
import jwt
import requests
import sqlalchemy
from fideslang.models import DatasetField, FidesModel
from fideslang.validation import FidesValidationError
from loguru import logger
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from fides.connectors.models import ConnectorAuthFailureException

logger.bind(name="server_api")

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


def validate_db_engine(connection_string: str) -> None:
    """
    Use SQLAlchemy to create a DB engine.
    """
    try:
        engine = sqlalchemy.create_engine(connection_string)
        with engine.begin() as connection:
            connection.execute("SELECT 1")
    except SQLAlchemyError as error:
        raise ConnectorAuthFailureException(error)


def get_db_engine(connection_string: str) -> Engine:
    """
    Use SQLAlchemy to create a DB engine.
    """
    try:
        engine = sqlalchemy.create_engine(
            connection_string, connect_args={"connect_timeout": 10}
        )
    except Exception as err:
        raise Exception("Failed to create engine!") from err

    try:
        with engine.begin() as connection:
            connection.execute("SELECT 1")
    except Exception as err:
        raise Exception(f"Database connection failed with engine:\n{engine}!") from err
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
        "Authorization": f"Bearer {jwt_encode(1, api_key)}",
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


def get_manifest_list(manifests_dir: str) -> List[str]:
    """Get a list of manifest files from the manifest directory."""
    yml_endings = ["yml", "yaml"]

    if isfile(manifests_dir) and manifests_dir.split(".")[-1] in yml_endings:
        return [manifests_dir]

    manifest_list = []
    for yml_ending in yml_endings:
        manifest_list += glob.glob(f"{manifests_dir}/**/*.{yml_ending}", recursive=True)

    return manifest_list


def check_fides_key(proposed_fides_key: str) -> str:
    """
    A helper function to automatically sanitize
    an invalid FidesKey.
    """
    try:
        FidesModel(fides_key=proposed_fides_key)
        return proposed_fides_key
    except FidesValidationError as error:
        echo_red(error)
        return sanitize_fides_key(proposed_fides_key)


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
    appended to the fides_key of a dataset
    """
    fides_key_uuid = sha1(
        "-".join([database_host, database_name, proposed_fides_key]).encode()
    )
    return f"{proposed_fides_key}_{fides_key_uuid.hexdigest()[:10]}"


def git_is_dirty(dir_to_check: str = ".") -> bool:
    """
    Checks to see if the local repo has unstaged changes.
    Can also specify a directory to check.
    """

    try:
        from git.repo import Repo
        from git.repo.fun import is_git_dir
    except ImportError:
        print("Git executable not detected, skipping git check...")
        return False

    git_dir_path = ".git/"
    if not is_git_dir(git_dir_path):
        print(f"No git repo detected at '{git_dir_path}', skipping git check...")
        return False

    repo = Repo()
    git_session = repo.git()

    dirty_phrases = ["Changes not staged for commit:", "Untracked files:"]
    git_status = git_session.status(dir_to_check).split("\n")
    is_dirty = any(phrase in git_status for phrase in dirty_phrases)
    return is_dirty
