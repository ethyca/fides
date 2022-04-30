from os import getenv

import nox

# Sets the default session to `--list`
nox.options.sessions = []

###############
## CONSTANTS ##
###############
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
WITH_TEST_CONFIG = "-f tests/test_config.toml"

# Image Names & Tags
REGISTRY = "ethyca"
IMAGE_NAME = "fidesctl"
IMAGE = f"{REGISTRY}/{IMAGE_NAME}"
IMAGE_LOCAL = f"{IMAGE}:local"
IMAGE_LATEST = f"{IMAGE}:latest"

# Disable TTY to perserve output within Github Actions logs
# CI env variable is always set to true in Github Actions
# The else statement is required due to the way commmands are structured and is arbitrary.
CI_ARGS = "--no-TTY" if getenv("CI") else "--user=root"

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

#########
## Dev ##
#########
@nox.session()
def reset_db(session: nox.Session) -> None:
    """Reset the database."""
    build_local(session)
    session.notify("teardown")
    session.run(*START_APP, external=True)
    reset_db_command = (*RUN, "fidesctl", "db", "reset", "-y")
    session.run(*reset_db_command, external=True)


@nox.session()
def api(session: nox.Session) -> None:
    """Spin up the webserver."""
    build_local(session)
    session.notify("teardown")
    run_in_background = ("docker-compose", "up", IMAGE_NAME)
    session.run(*run_in_background, external=True)


@nox.session()
def cli(session: nox.Session) -> None:
    """Spin up a local development shell."""
    build_local(session)
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_shell = (*RUN, "/bin/bash")
    session.run(*run_shell, external=True)


@nox.session()
def cli_integration(session: nox.Session) -> None:
    """Spin up a local development shell with integration images spun up."""
    build_local(session)
    session.notify("teardown")
    session.run(
        "docker-compose",
        "-f",
        "docker-compose.yml",
        "-f",
        "docker-compose.integration-tests.yml",
        "up",
        "-d",
        IMAGE_NAME,
        external=True,
    )
    run_shell = (*RUN, "/bin/bash")
    session.run(*run_shell, external=True)


@nox.session()
def db(session: nox.Session) -> None:
    """Spin up the application database in the background."""
    db_up = ("docker-compose", "up", "-d", "fidesctl-db")
    session.run(*db_up, external=True)


############
## Docker ##
############
@nox.session()
def build(session: nox.Session) -> None:
    """Build the Docker container for fidesctl."""
    session.run(
        "docker",
        "build",
        "--target=prod",
        "--tag",
        f"{IMAGE}:{get_current_tag()}",
        ".",
        external=True,
    )


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


##########
## Docs ##
##########
def docs_build(session: nox.Session) -> None:
    """Build docs from the source code."""
    run_shell = (*RUN, "python", "generate_docs.py", "docs/fides/docs/")
    session.run(*run_shell, external=True)


@nox.session()
def docs_build_local(session: nox.Session) -> None:
    """Build a new image then build docs from the source code."""
    build_local(session)
    session.notify("teardown")
    docs_build(session)


@nox.session()
def docs_build_ci(session: nox.Session) -> None:
    """Build docs from the source code without building a new image."""
    session.notify("teardown")
    docs_build(session)


@nox.session()
def docs_serve(session: nox.Session) -> None:
    """Build docs from the source code."""
    docs_build_local(session)
    session.notify("teardown")
    session.run("docker-compose", "build", "docs", external=True)
    run_shell = (
        "docker-compose",
        "run",
        "--rm",
        "--service-ports",
        CI_ARGS,
        "docs",
        "/bin/bash",
        "-c",
        "pip install -e /fides[all] && mkdocs serve --dev-addr=0.0.0.0:8000",
    )
    session.run(*run_shell, external=True)


@nox.session()
def docs_check(session: nox.Session) -> None:
    """Build docs from the source code."""
    docs_build_ci(session)
    session.notify("teardown")
    session.run("docker-compose", "build", "docs", external=True)
    run_shell = (
        "docker-compose",
        "run",
        "--rm",
        "--service-ports",
        CI_ARGS,
        "docs",
        "/bin/bash",
        "-c",
        "pip install -e /fides[all] && mkdocs build",
    )
    session.run(*run_shell, external=True)


########
## CI ##
########
RUN_STATIC_ANALYSIS = (*RUN_NO_DEPS, "nox", "-s")


@nox.session()
def check_all(session: nox.Session) -> None:
    """Run all of the Docker versions of the CI checks."""
    teardown(session)
    build_local_prod(session)
    check_install(session)
    fidesctl(session)
    fidesctl_db_scan(session)
    isort(session)
    black(session)
    pylint(session)
    mypy(session)
    xenon(session)
    pytest_unit(session)
    pytest_integration(session)


@nox.session()
def black(session: nox.Session) -> None:
    """Run the 'black' style linter."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "black")
    else:
        run_command = ("black", "--check", "src", "tests")
    session.run(*run_command, external=True)


@nox.session()
def isort(session: nox.Session) -> None:
    """Run the 'isort' import linter."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "isort")
    else:
        run_command = ("isort", "--check-only", "src", "tests")
    session.run(*run_command, external=True)


@nox.session()
def check_install(session: nox.Session) -> None:
    """Run the 'isort' import linter."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "check_install")
    else:
        run_command = ("fidesctl", *(WITH_TEST_CONFIG), "--version")
    session.run(*run_command, external=True)


@nox.session()
def fidesctl(session: nox.Session) -> None:
    """Run the 'isort' import linter."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "fidesctl")
    else:
        run_command = ("fidesctl", "--local", *(WITH_TEST_CONFIG), "evaluate")
    session.run(*run_command, external=True)


# check-install:
# 	@echo "Checking that fidesctl is installed..."
# 	@$(RUN_NO_DEPS) fidesctl ${WITH_TEST_CONFIG} --version

# .PHONY: fidesctl
# fidesctl:
# 	@$(RUN_NO_DEPS) fidesctl --local ${WITH_TEST_CONFIG} evaluate

# fidesctl-db-scan:
# 	@$(START_APP)
# 	@$(RUN) fidesctl ${WITH_TEST_CONFIG} scan dataset db \
# 	"postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test"

# mypy:
# 	@$(RUN_NO_DEPS) mypy

# pylint:
# 	@$(RUN_NO_DEPS) pylint src/

# pytest-unit:
# 	@$(START_APP)
# 	@$(RUN_NO_DEPS) pytest -x -m unit

# pytest-integration:
# 	@$(START_APP)
# 	@docker compose run --rm $(CI_ARGS) $(IMAGE_NAME) \
# 	pytest -x -m integration
# 	@make teardown

# pytest-external:
# 	@docker compose -f docker-compose.yml -f docker-compose.integration-tests.yml up -d $(IMAGE_NAME)
# 	@docker compose run \
# 	-e SNOWFLAKE_FIDESCTL_PASSWORD \
# 	-e REDSHIFT_FIDESCTL_PASSWORD \
# 	-e AWS_ACCESS_KEY_ID \
# 	-e AWS_SECRET_ACCESS_KEY \
# 	-e AWS_DEFAULT_REGION \
# 	-e OKTA_CLIENT_TOKEN \
# 	--rm $(CI_ARGS) $(IMAGE_NAME) \
# 	pytest -x -m external
# 	@make teardown

# xenon:
# 	@$(RUN_NO_DEPS) xenon src \
# 	--max-absolute B \
# 	--max-modules B \
# 	--max-average A \
# 	--ignore "data, tests, docs" \
# 	--exclude "src/fidesctl/_version.py"
