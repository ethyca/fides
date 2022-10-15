"""Define constants to be used across the noxfiles."""
from os import getenv

# Files
COMPOSE_FILE = "docker-compose.yml"
INTEGRATION_COMPOSE_FILE = "docker-compose.integration-tests.yml"
WITH_TEST_CONFIG = ("-f", "tests/ctl/test_config.toml")

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fides"
COMPOSE_SERVICE_NAME = "fides"

# Files
COMPOSE_FILE = "docker-compose.yml"
INTEGRATION_COMPOSE_FILE = "docker-compose.integration-tests.yml"
INTEGRATION_POSTGRES_COMPOSE_FILE = "docker/docker-compose.integration-postgres.yml"

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fides"
IMAGE = f"{REGISTRY}/{IMAGE_NAME}"
IMAGE_LOCAL = f"{IMAGE}:local"
IMAGE_LOCAL_UI = f"{IMAGE}:local-ui"
IMAGE_DEV = f"{IMAGE}:dev"
IMAGE_LATEST = f"{IMAGE}:latest"

# Disable TTY to perserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
# The else statement is required due to the way commmands are structured and is arbitrary.
CI_ARGS = "-T" if getenv("CI") else "--user=root"

# If FIDES__CLI__ANALYTICS_ID is set in the local environment, use its value as the analytics_id
ANALYTICS_ID_OVERRIDE = ("-e", "FIDES__CLI__ANALYTICS_ID")
ANALYTICS_OPT_OUT = ("-e", "ANALYTICS_OPT_OUT")

# Reusable Commands
RUN = (
    "docker",
    "compose",
    "run",
    "-e",
    "VAULT_ADDR",
    "-e",
    "VAULT_NAMESPACE",
    "-e",
    "VAULT_TOKEN",
    "--rm",
    *ANALYTICS_ID_OVERRIDE,
    *ANALYTICS_OPT_OUT,
    CI_ARGS,
    COMPOSE_SERVICE_NAME,
)
RUN_NO_DEPS = (
    "docker",
    "compose",
    "run",
    "--no-deps",
    "--rm",
    *ANALYTICS_ID_OVERRIDE,
    CI_ARGS,
    IMAGE_NAME,
)
START_APP = ("docker", "compose", "up", "--wait", COMPOSE_SERVICE_NAME)
START_APP_EXTERNAL = (
    "docker",
    "compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    INTEGRATION_COMPOSE_FILE,
    "up",
    "--wait",
    COMPOSE_SERVICE_NAME,
)
START_APP_WITH_EXTERNAL_POSTGRES = (
    "docker",
    "compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    INTEGRATION_POSTGRES_COMPOSE_FILE,
    "up",
    "--wait",
    "fides",
    "postgres_example",
)
