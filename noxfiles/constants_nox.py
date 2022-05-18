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


# Files
COMPOSE_FILE = "docker-compose.yml"
INTEGRATION_COMPOSE_FILE = "docker-compose.integration-tests.yml"
WITH_TEST_CONFIG = ("-f", "tests/test_config.toml")

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fidesctl"
IMAGE = f"{REGISTRY}/{IMAGE_NAME}"
IMAGE_LOCAL = f"{IMAGE}:local"
IMAGE_LATEST = f"{IMAGE}:latest"

# Disable TTY to perserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
# The else statement is required due to the way commmands are structured and is arbitrary.
CI_ARGS = "-T" if getenv("CI") else "--user=root"

# If FIDESCTL__CLI__ANALYTICS_ID is set in the local environment, use its value as the analytics_id
ANALYTICS_ID_OVERRIDE = ("-e", "FIDESCTL__CLI__ANALYTICS_ID")

# Reusable Commands
RUN = ("docker-compose", "run", "--rm", *ANALYTICS_ID_OVERRIDE, CI_ARGS, IMAGE_NAME)
RUN_NO_DEPS = (
    "docker-compose",
    "run",
    "--no-deps",
    "--rm",
    *ANALYTICS_ID_OVERRIDE,
    CI_ARGS,
    IMAGE_NAME,
)
START_APP = ("docker-compose", "up", "-d", IMAGE_NAME)
