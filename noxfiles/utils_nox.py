"""Contains various utility-related nox sessions."""
from subprocess import run, PIPE
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
def check_docker_compose_version(session: nox.Session) -> bool:
    """Verify the Docker Compose version."""
    required_docker_compose_version = "2.10.2"
    raw = run("docker-compose --version", stdout=PIPE)
    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    docker_compose_version = parsed.split("v")[-1]
    print(parsed)
    version_is_valid = docker_compose_version >= required_docker_compose_version
    if not version_is_valid:
        session.error(
            f"Docker Compose version is not compatible, please update to at least version {required_docker_compose_version}!"
        )
    return version_is_valid


@nox.session()
def check_docker_version(session: nox.Session) -> bool:
    """Verify the Docker version."""
    required_docker_version = "20.10.17"
    raw = run("docker --version", stdout=PIPE)
    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    docker_version = parsed.split("v")[-1]
    print(parsed)
    version_is_valid = docker_version >= required_docker_version
    if not version_is_valid:
        session.error(
            f"Docker version is not compatible, please update to at least version {required_docker_version}!"
        )
    return version_is_valid


def install_requirements(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.install("-r", "dev-requirements.txt")
