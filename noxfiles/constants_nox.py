"""Define constants to be used across the noxfiles."""
from os import getcwd, getenv

# Files
COMPOSE_FILE = "docker-compose.yml"
INTEGRATION_COMPOSE_FILE = "docker-compose.integration-tests.yml"
INTEGRATION_POSTGRES_COMPOSE_FILE = "docker/docker-compose.integration-postgres.yml"
TEST_ENV_COMPOSE_FILE = "docker-compose.test-env.yml"
REMOTE_DEBUG_COMPOSE_FILE = "docker-compose.remote-debug.yml"
WITH_TEST_CONFIG = ("-f", "tests/ctl/test_config.toml")

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fides"
CONTAINER_NAME = "fides-fides-1"
COMPOSE_SERVICE_NAME = "fides"

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fides"
IMAGE = f"{REGISTRY}/{IMAGE_NAME}"
IMAGE_LOCAL = f"{IMAGE}:local"
IMAGE_LOCAL_UI = f"{IMAGE}:local-ui"
IMAGE_DEV = f"{IMAGE}:dev"
IMAGE_SAMPLE = f"{IMAGE}:sample"
IMAGE_LATEST = f"{IMAGE}:latest"

# Image names for the secondary apps
PRIVACY_CENTER_IMAGE = f"{REGISTRY}/fides-privacy-center"
SAMPLE_APP_IMAGE = f"{REGISTRY}/fides-sample-app"

# Image names for 3rd party apps
CYPRESS_IMAGE = "cypress/included:12.3.0"

# Helpful paths
CWD = getcwd()

# Disable TTY to perserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
# The else statement is required due to the way commmands are structured and is arbitrary.
CI_ARGS = "-T" if getenv("CI") else "--user=root"
CI_ARGS_EXEC = "-t" if not getenv("CI") else "--user=root"

# If FIDES__CLI__ANALYTICS_ID is set in the local environment, use its value as the analytics_id
ANALYTICS_ID_OVERRIDE = ("-e", "FIDES__CLI__ANALYTICS_ID")
ANALYTICS_OPT_OUT = ("-e", "ANALYTICS_OPT_OUT")

# Reusable Commands
LOGIN = (
    "docker",
    "exec",
    "fides-fides-1",
    "fides",
    "user",
    "login",
    "-u",
    "root_user",
    "-p",
    "Testpassword1!",
)
EXEC = (
    "docker",
    "exec",
    *ANALYTICS_ID_OVERRIDE,
    CI_ARGS_EXEC,
    CONTAINER_NAME,
)
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
START_TEST_ENV = (
    "docker",
    "compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    TEST_ENV_COMPOSE_FILE,
    "up",
    "--wait",
    COMPOSE_SERVICE_NAME,
)
START_APP_REMOTE_DEBUG = (
    "docker",
    "compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    REMOTE_DEBUG_COMPOSE_FILE,
    "up",
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
RUN_CYPRESS_TESTS = (
    "docker",
    "run",
    "-t",
    "--network=host",
    "-v",
    f"{CWD}/clients/cypress-e2e:/e2e",
    "-w",
    "/e2e",
    CYPRESS_IMAGE,
)
