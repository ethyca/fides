"""Define constants to be used across the noxfiles."""

from os import getcwd, getenv

# Files
COMPOSE_FILE = "docker-compose.yml"
INTEGRATION_COMPOSE_FILE = "./docker-compose.integration-tests.yml"
INTEGRATION_POSTGRES_COMPOSE_FILE = "./docker/docker-compose.integration-postgres.yml"
REMOTE_DEBUG_COMPOSE_FILE = "docker-compose.remote-debug.yml"
SAMPLE_PROJECT_COMPOSE_FILE = "./src/fides/data/sample_project/docker-compose.yml"
WITH_TEST_CONFIG = ("-f", "tests/ctl/test_config.toml")

COMPOSE_FILE_LIST = {
    COMPOSE_FILE,
    SAMPLE_PROJECT_COMPOSE_FILE,
    INTEGRATION_COMPOSE_FILE,
    "docker/docker-compose.integration-mariadb.yml",
    "docker/docker-compose.integration-mongodb.yml",
    "docker/docker-compose.integration-mysql.yml",
    "docker/docker-compose.integration-postgres.yml",
    "docker/docker-compose.integration-mssql.yml",
}

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fides"
CONTAINER_NAME = "fides"
COMPOSE_SERVICE_NAME = "fides"

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fides"
IMAGE = f"{REGISTRY}/{IMAGE_NAME}"
IMAGE_LOCAL = f"{IMAGE}:local"
IMAGE_LOCAL_UI = f"{IMAGE}:local-ui"
IMAGE_LOCAL_PC = f"{IMAGE}:local-pc"

# Image names for the secondary apps
PRIVACY_CENTER_IMAGE = f"{REGISTRY}/fides-privacy-center"
SAMPLE_APP_IMAGE = f"{REGISTRY}/fides-sample-app"

# Constant tag suffixes for published images
DEV_TAG_SUFFIX = "dev"
PRERELEASE_TAG_SUFFIX = "prerelease"
RC_TAG_SUFFIX = "rc"
LATEST_TAG_SUFFIX = "latest"

# Image names for 3rd party apps
CYPRESS_IMAGE = "cypress/included:12.8.1"

# Helpful paths
CWD = getcwd()

# Disable TTY to preserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
# The else statement is required due to the way commands are structured and is arbitrary.
CI_ARGS = "-T" if getenv("CI") else "--user=fidesuser"
CI_ARGS_EXEC = "-t" if not getenv("CI") else "--user=fidesuser"

# If FIDES__CLI__ANALYTICS_ID is set in the local environment, use its value as the analytics_id
ANALYTICS_ID_OVERRIDE = ("-e", "FIDES__CLI__ANALYTICS_ID")
ANALYTICS_OPT_OUT = ("-e", "ANALYTICS_OPT_OUT")

# Reusable Commands
LOGIN = (
    "docker",
    "exec",
    CONTAINER_NAME,
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
    *ANALYTICS_OPT_OUT,
    *ANALYTICS_ID_OVERRIDE,
    CI_ARGS_EXEC,
    CONTAINER_NAME,
)
EXEC_IT = (
    "docker",
    "exec",
    "-it",
    *ANALYTICS_OPT_OUT,
    *ANALYTICS_ID_OVERRIDE,
    CI_ARGS_EXEC,
    CONTAINER_NAME,
)
RUN = (
    "docker-compose",
    "run",
    "--rm",
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
    f"{CWD}/clients/cypress-e2e:/cypress-e2e",
    "-w",
    "/cypress-e2e",
    "--entrypoint=",
    "-e",
    "CYPRESS_VIDEO=false",
    CYPRESS_IMAGE,
    "/bin/bash",
    "-c",
    "npm install && cypress run",
)
