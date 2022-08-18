"""Contains various utility-related nox sessions."""
import nox
from constants_nox import COMPOSE_FILE, INTEGRATION_COMPOSE_FILE
from run_infrastructure import run_infrastructure

COMPOSE_DOWN = (
    "docker-compose",
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
def create_user(session: nox.Session) -> None:
    """Create a super user in the fidesops database."""
    run_infrastructure(datastores=["postgres"], run_create_superuser=True)


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
    session.run("docker", "system", "prune", "--force", external=True)
    print("Clean Complete!")


@nox.session()
def teardown(session: nox.Session) -> None:
    """Tear down the docker dev environment."""
    if session.posargs[0] == "volumes":
        session.run(*COMPOSE_DOWN_VOLUMES, external=True)
    else:
        session.run(*COMPOSE_DOWN, external=True)
    print("Teardown complete")


def install_requirements(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.install("-r", "dev-requirements.txt")
