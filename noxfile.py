# Add all of the makefile functionality
from git import Repo

import nox

###############
## CONSTANTS ##
###############
def get_current_tag() -> str:
    """Get the current git tag."""
    repo = Repo()
    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    current_tag = git_session.describe("--tags", "--dirty", "--always")
    return current_tag


# Files
COMPOSE_FILE = "docker-compose.yml"
INTEGRATION_COMPOSE_FILE = "docker-compose.integration-tests.yml"
WITH_TEST_CONFIG = "-f tests/test_config.toml"

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_TAG = get_current_tag()
IMAGE_NAME = "fidesctl"
IMAGE = f"{REGISTRY}/{IMAGE_NAME}:{IMAGE_TAG}"
IMAGE_LOCAL = f"{REGISTRY}/{IMAGE_NAME}:local"
IMAGE_LATEST = f"{REGISTRY}/{IMAGE_NAME}:latest"

# Requirements
DOCKER = "docker>=5"
DOCKER_COMPOSE = "docker-compose>=1.29.2"

############
## Docker ##
############


@nox.session()
def build(session: nox.Session) -> None:
    """Build the Docker container for fidesctl."""
    session.run("docker", "build", "--target=prod", "--tag", IMAGE, ".", external=True)


@nox.session()
def build_local(session: nox.Session) -> None:
    """Build the Docker container for fidesctl tagged 'local'."""
    session.run(
        "docker", "build", "--target=dev", "--tag", IMAGE_LOCAL, ".", external=True
    )


@nox.session()
def build_local_prod(session: nox.Session) -> None:
    """Build the Docker container for fidesctl tagged 'local' with the prod stage target."""
    session.run(
        "docker", "build", "--target=prod", "--tag", IMAGE_LOCAL, ".", external=True
    )


@nox.session()
def push(session: nox.Session) -> None:
    """Push the Docker container for fidesctl."""
    session.run("docker", "tag", IMAGE, IMAGE_LATEST, external=True)
    session.run("docker", "push", IMAGE, external=True)
    session.run("docker", "push", IMAGE_LATEST, external=True)


###########
## Utils ##
###########


@nox.session()
def clean(session: nox.Session) -> None:
    """
    Clean up docker containers, remove orphans, remove volumes
    and prune images related to this project.
    """
    session.run(
        "docker-compose",
        "-f",
        COMPOSE_FILE,
        "-f",
        INTEGRATION_COMPOSE_FILE,
        "down",
        "--remove-orphans",
        "--volumes",
        "--rmi",
        "all",
        external=True,
    )
    session.run("docker", "system", "prune", "--force", external=True)
    print("Clean Complete!")


@nox.session()
def teardown(session: nox.Session) -> None:
    """Tear down the docker dev environment."""
    session.run(
        "docker-compose",
        "-f",
        COMPOSE_FILE,
        "-f",
        INTEGRATION_COMPOSE_FILE,
        "down",
        "--remove-orphans",
        external=True,
    )
    print("Teardown complete")
