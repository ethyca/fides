"""Contains various utility-related nox sessions."""
from subprocess import PIPE, run

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


@nox.session()
def check_docker_version(session: nox.Session) -> bool:
    """Verify the Docker version."""
    raw = run("docker --version", stdout=PIPE, check=True, shell=True)
    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    docker_version = parsed.split("version ")[-1].split(",")[0]
    print(parsed)
    version_is_valid = int(docker_version.replace(".", "")) >= int(
        REQUIRED_DOCKER_VERSION.replace(".", "")
    )
    if not version_is_valid:
        session.error(
            f"Your Docker version (v{docker_version}) is not compatible, please update to at least version {REQUIRED_DOCKER_VERSION}!"
        )
    return version_is_valid


def install_requirements(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.install("-r", "dev-requirements.txt")
