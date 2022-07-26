"""Define constants to be used across the noxfiles."""
from os import getenv


def get_current_tag() -> str:
    """Get the current git tag."""
    from git.repo import Repo

    repo = Repo()
    git_session = repo.git()
    git_session.fetch("--force", "--tags")
    current_tag = git_session.describe("--tags", "--dirty", "--always")
    return current_tag


COMPOSE_SERVICE_NAME = "webserver"

# Files
COMPOSE_FILE = "docker-compose.yml"
INTEGRATION_COMPOSE_FILE = "docker-compose.integration-tests.yml"
WITH_TEST_CONFIG = ("-f", "tests/test_config.toml")

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fidesops"
IMAGE = f"{REGISTRY}/{IMAGE_NAME}"
IMAGE_LOCAL = f"{IMAGE}:local"
IMAGE_LOCAL_UI = f"{IMAGE}:local-ui"
IMAGE_DEV = f"{IMAGE}:dev"
IMAGE_LATEST = f"{IMAGE}:latest"

# Disable TTY to perserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
# The else statement is required due to the way commmands are structured and is arbitrary.
CI_ARGS = "-T" if getenv("CI") else "--user=root"

ANALYTICS_OPT_OUT = ("-e", "ANALYTICS_OPT_OUT")

# Reusable Commands
RUN = (
    "docker-compose",
    "run",
    "--rm",
    *ANALYTICS_OPT_OUT,
    CI_ARGS,
    COMPOSE_SERVICE_NAME,
)
RUN_NO_DEPS = (
    "docker-compose",
    "run",
    "--no-deps",
    "--rm",
    *ANALYTICS_OPT_OUT,
    CI_ARGS,
    COMPOSE_SERVICE_NAME,
)
START_APP = ("docker-compose", "up", "-d", COMPOSE_SERVICE_NAME)
START_APP_EXTERNAL = (
    "docker-compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    INTEGRATION_COMPOSE_FILE,
    "up",
    "-d",
    COMPOSE_SERVICE_NAME,
)
