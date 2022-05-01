"""Contains the nox sessions for running development environments."""
import nox
from constants_nox import COMPOSE_FILE, INTEGRATION_COMPOSE_FILE

COMPOSE_DOWN = (
    "docker-compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    INTEGRATION_COMPOSE_FILE,
    "down",
    "--remove-orphans",
)


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
    session.run(*COMPOSE_DOWN, external=True)
    print("Teardown complete")
