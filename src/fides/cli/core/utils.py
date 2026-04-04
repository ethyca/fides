import glob
from os.path import isfile
from typing import List

from fideslang.models import FidesModel
from loguru import logger
from pydantic import ValidationError

from fides.common.utils import echo_red
from fides.common.utils import (
    generate_unique_fides_key as generate_unique_fides_key,
)
from fides.common.utils import get_all_level_fields as get_all_level_fields
from fides.common.utils import get_db_engine as get_db_engine
from fides.common.utils import sanitize_fides_key as sanitize_fides_key
from fides.common.utils import validate_db_engine as validate_db_engine

logger.bind(name="server_api")


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
