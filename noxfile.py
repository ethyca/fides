"""
This file aggregates nox commands for various development tasks.
"""
import webbrowser
import shutil
import sys
from os.path import isfile
from subprocess import PIPE, CalledProcessError, run
from typing import List

import nox

sys.path.append("noxfiles")
# pylint: disable=unused-wildcard-import, wildcard-import, wrong-import-position
from ci_nox import *
from dev_nox import *
from docker_nox import *
from docs_nox import *
from git_nox import *
from utils_nox import *

# pylint: enable=unused-wildcard-import, wildcard-import, wrong-import-position

REQUIRED_DOCKER_VERSION = "20.10.17"

nox.options.sessions = ["open_docs"]

# This is important for caching pip installs
nox.options.reuse_existing_virtualenvs = True


@nox.session()
def open_docs(session: nox.Session) -> None:
    """Open the webpage for the developer/contribution docs."""
    docs_url = "https://ethyca.github.io/fides/stable/development/overview/"
    webbrowser.open(docs_url)


@nox.session()
def usage(session: nox.Session) -> None:
    """Prints the documentation for a nox session provided: `nox -s usage -- <session>`."""

    if not session.posargs:
        session.error("Please provide a session name, such as `clean`")

    command = session.posargs[0]

    if not command in globals():
        session.error(
            "Sorry, this isn't a valid nox session.\nExamples: `clean`, `build`, `pytest_ctl`"
        )

    session.log(globals()[command].__doc__)


def check_for_env_file() -> None:
    """Create a .env file if none exists."""
    env_file_example = "example.env"
    env_file = ".env"
    if not isfile(env_file):
        print(
            f"Creating env file for local testing & development from {env_file_example}: {env_file}"
        )
        shutil.copy(env_file_example, env_file)


# Add a command that opens the docs


def convert_semver_to_list(semver: str) -> List[int]:
    """
    Convert a standard semver string to a list of ints

    '2.10.7' -> [2,10,7]
    """
    return [int(x) for x in semver.split(".")]


def compare_semvers(version_a: List[int], version_b: List[int]) -> bool:
    """
    Determine which semver-style list of integers is larger.

    [2,10,3], [2,10,2] -> True
    [3,1,3], [2,10,2] -> True
    [2,10,2], [2,10,2] -> True
    [1,1,3], [2,10,2] -> False
    """

    major, minor, patch = [0, 1, 2]
    # Compare Major Versions
    if version_a[major] > version_b[major]:
        return True
    if version_a[major] < version_b[major]:
        return False

    # If Major Versions Match, Compare Minor Versions
    if version_a[minor] > version_b[minor]:
        return True
    if version_a[minor] < version_b[minor]:
        return False

    # If Both Major & Minor Versions Match, Compare Patch Versions
    if version_a[patch] < version_b[patch]:
        return False

    return True


def check_docker_version() -> bool:
    """Verify the Docker version."""
    try:
        raw = run("docker --version", stdout=PIPE, check=True, shell=True)
    except CalledProcessError:
        raise SystemExit("Error: Command 'docker' is not available.")

    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    # We need to handle multiple possible version formats here
    # Docker version 20.10.17, build 100c701
    # Docker version 20.10.18+azure-1, build b40c2f6
    docker_version = parsed.split("version ")[-1].split(",")[0].split("+")[0]
    print(parsed)

    split_docker_version = convert_semver_to_list(docker_version)
    split_required_docker_version = convert_semver_to_list(REQUIRED_DOCKER_VERSION)

    if len(split_docker_version) != 3:
        raise SystemExit(
            "Error: Docker version format is invalid, expecting semver format. Please upgrade to a more recent version and try again"
        )

    version_is_valid = compare_semvers(
        split_docker_version, split_required_docker_version
    )
    if not version_is_valid:
        raise SystemExit(
            f"Error: Your Docker version (v{docker_version}) is not compatible, please update to at least version {REQUIRED_DOCKER_VERSION}!"
        )
    return version_is_valid


# Run startup checks
check_docker_version()
check_for_env_file()
