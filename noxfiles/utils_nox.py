"""Contains various utility-related nox sessions."""
from subprocess import PIPE, run
from typing import List

import nox

from constants_nox import COMPOSE_FILE, INTEGRATION_COMPOSE_FILE
from run_infrastructure import run_infrastructure

COMPOSE_DOWN = (
    "docker",
    "compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    INTEGRATION_COMPOSE_FILE,
    "-f",
    "docker/docker-compose.integration-mariadb.yml",
    "-f",
    "docker/docker-compose.integration-mongodb.yml",
    "-f",
    "docker/docker-compose.integration-mysql.yml",
    "-f",
    "docker/docker-compose.integration-postgres.yml",
    "-f",
    "docker/docker-compose.integration-mssql.yml",
    "down",
    "--remove-orphans",
)
COMPOSE_DOWN_VOLUMES = COMPOSE_DOWN + ("--volumes",)
REQUIRED_DOCKER_VERSION = "20.10.17"
REQUIRED_DOCKER_COMPOSE_VERSION = "2.10.2"


@nox.session()
def seed_test_data(session: nox.Session) -> None:
    """Seed test data in the Postgres application database."""
    run_infrastructure(datastores=["postgres"], run_create_test_data=True)


@nox.session()
def clean(session: nox.Session) -> None:
    """
    Clean up docker containers, remove orphans, remove volumes
    and prune images related to this project.
    """
    clean_command = (*COMPOSE_DOWN, "--volumes", "--rmi", "all")
    session.run(*clean_command, external=True)
    session.run("docker", "system", "prune", "--force", "--all", external=True)
    print("Clean Complete!")


@nox.session()
def teardown(session: nox.Session) -> None:
    """Tear down the docker dev environment."""
    if "volumes" in session.posargs:
        session.run(*COMPOSE_DOWN_VOLUMES, external=True)
    else:
        session.run(*COMPOSE_DOWN, external=True)
    print("Teardown complete")


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


@nox.session()
def check_docker_compose_version(session: nox.Session) -> bool:
    """Verify the Docker Compose version."""
    raw = run("docker-compose --version", stdout=PIPE, check=True, shell=True)
    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    print(parsed)

    try:
        docker_compose_version = parsed.split("v")[-1]
        split_docker_compose = convert_semver_to_list(docker_compose_version)
    except ValueError:
        docker_compose_version = parsed.split("version ")[-1].split(",")[0]
        split_docker_compose = convert_semver_to_list(docker_compose_version)

    if len(split_docker_compose) != 3:
        session.error(
            "Docker Compose version format is invalid, expecting semver format. Please upgrade to a more recent version and try again"
        )

    split_required_docker_compose_version = convert_semver_to_list(
        REQUIRED_DOCKER_COMPOSE_VERSION
    )
    version_is_valid = compare_semvers(
        split_docker_compose, split_required_docker_compose_version
    )
    if not version_is_valid:
        session.error(
            f"Your Docker Compose version (v{docker_compose_version})is not compatible, please update to at least version {REQUIRED_DOCKER_COMPOSE_VERSION}!"
        )
    return version_is_valid


@nox.session()
def check_docker_version(session: nox.Session) -> bool:
    """Verify the Docker version."""
    raw = run("docker --version", stdout=PIPE, check=True, shell=True)
    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    docker_version = parsed.split("version ")[-1].split(",")[0]
    print(parsed)

    split_docker_version = [int(x) for x in docker_version.split(".")]
    split_required_docker_version = convert_semver_to_list(REQUIRED_DOCKER_VERSION)

    if len(split_docker_version) != 3:
        session.error(
            "Docker version format is invalid, expecting semver format. Please upgrade to a more recent version and try again"
        )

    version_is_valid = compare_semvers(
        split_docker_version, split_required_docker_version
    )
    if not version_is_valid:
        session.error(
            f"Your Docker version (v{docker_version}) is not compatible, please update to at least version {REQUIRED_DOCKER_VERSION}!"
        )
    return version_is_valid


def install_requirements(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.install("-r", "dev-requirements.txt")
