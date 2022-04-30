from git.repo import Repo

import nox

nox.options.sessions = []

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

# Disable TTY to perserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
CI_ARGS = "--no-TTY"
# ifeq "$(CI)" "true"
#     CI_ARGS:=--no-TTY
# endif

# If FIDESCTL__CLI__ANALYTICS_ID is set in the local environment, use its value as the analytics_id
ANALYTICS_ID_OVERRIDE = ("-e", "FIDESCTL__CLI__ANALYTICS_ID")
# Reusable Commands
RUN = ("docker-compose", "run", "--rm", ANALYTICS_ID_OVERRIDE, CI_ARGS, IMAGE_NAME)
RUN_NO_DEPS = (
    "docker-compose",
    "run",
    "--no-deps",
    "--rm",
    ANALYTICS_ID_OVERRIDE,
    CI_ARGS,
    IMAGE_NAME,
)
START_APP = ("docker-compose", "up", "-d", IMAGE_NAME)

#########
## Dev ##
#########
@nox.session()
def reset_db(session: nox.Session) -> None:
    """Reset the database."""
    build_local(session)
    session.run(START_APP)
    session.run(RUN, "fidesctl", "db", "reset", "-y")
    session.notify("teardown")


@nox.session()
def api(session: nox.Session) -> None:
    """Spin up the webserver."""
    build_local(session)
    session.run("docker-compose", "up", IMAGE_NAME, external=True)
    teardown(session)


@nox.session()
def cli(session: nox.Session) -> None:
    """Spin up a local development shell."""
    build_local(session)
    session.run("docker-compose", "up", IMAGE_NAME, external=True)
    session.run(RUN, "/bin/bash", external=True)
    teardown(session)


@nox.session()
def cli_integration(session: nox.Session) -> None:
    """Spin up a local development shell with integration images spun up."""
    session.notify("build_local")
    session.run(
        "docker-compose",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.integration-tests.yml",
        "up",
        "-d",
        IMAGE_NAME,
    )
    session.run(RUN, "/bin/bash")
    session.notify("teardown")


@nox.session()
def db(session: nox.Session) -> None:
    """Spin up the application database in the background."""
    session.run("docker", "compose", "up", "-d", "fidesctl-db")


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
