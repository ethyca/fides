import glob
import re
from hashlib import sha1
from os import getenv
from os.path import isfile
from pathlib import Path
from typing import Any, Dict, Iterator, List

import sqlalchemy
import toml
from fideslang.models import DatasetField, FidesModel
from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from fides.common.utils import echo_red
from fides.connectors.models import ConnectorAuthFailureException

logger.bind(name="server_api")


class Credentials(BaseModel):
    """
    User credentials for the CLI.
    """

    username: str
    user_id: str
    access_token: str


def get_db_engine(connection_string: str) -> Engine:
    """
    Use SQLAlchemy to create a DB engine.
    """

    # Pymssql doesn't support this arg
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
    Use SQLAlchemy to create a DB engine.
    """
    # Pymssql doesn't support this arg
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
    except SQLAlchemyError as error:
        raise ConnectorAuthFailureException(error)


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
    except ValidationError as error:
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


def write_credentials_file(credentials: Credentials, credentials_path: str) -> str:
    """Write the user credentials file."""
    with open(credentials_path, "w", encoding="utf-8") as credentials_file:
        credentials_file.write(toml.dumps(credentials.model_dump(mode="json")))
    return credentials_path


def get_credentials_path() -> str:
    """
    Returns the default credentials path or the path set as an environment variable.
    """
    default_credentials_file_path = f"{str(Path.home())}/.fides_credentials"
    credentials_path = getenv("FIDES_CREDENTIALS_PATH", default_credentials_file_path)
    return credentials_path


def read_credentials_file(
    credentials_path: str,
) -> Credentials:
    """Read and return the credentials file."""
    if not isfile(credentials_path):
        raise FileNotFoundError
    with open(credentials_path, "r", encoding="utf-8") as credentials_file:
        credentials = Credentials.model_validate(toml.load(credentials_file))
    return credentials


def create_auth_header(access_token: str) -> Dict[str, str]:
    """Given an access token, create an auth header."""
    auth_header = {
        "Authorization": f"Bearer {access_token}",
    }
    return auth_header


def get_auth_header(verbose: bool = True) -> Dict[str, str]:
    """
    Executes all of the logic required to form a valid auth header.
    """
    credentials_path = get_credentials_path()
    try:
        credentials = read_credentials_file(credentials_path=credentials_path)
    except FileNotFoundError:
        if verbose:
            echo_red("No credentials file found.")
        raise SystemExit(1)

    access_token = credentials.access_token
    auth_header = create_auth_header(access_token)
    return auth_header
