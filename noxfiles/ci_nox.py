"""Contains the nox sessions used during CI checks."""
import nox
from constants_nox import RUN, RUN_NO_DEPS, START_APP, WITH_TEST_CONFIG
from docker_nox import build_local_prod
from utils_nox import teardown

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
    """Check that fidesctl is installed."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "check_install")
    else:
        run_command = ("fidesctl", *(WITH_TEST_CONFIG), "--version")
    session.run(*run_command, external=True)


@nox.session()
def fidesctl(session: nox.Session) -> None:
    """Run a fidesctl evaluation."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "fidesctl")
    else:
        run_command = ("fidesctl", "--local", *(WITH_TEST_CONFIG), "evaluate")
    session.run(*run_command, external=True)


@nox.session()
def fidesctl_db_scan(session: nox.Session) -> None:
    """ "Scan the fidesctl application database to check for dataset discrepancies."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    run_command = (
        *RUN,
        "fidesctl",
        *(WITH_TEST_CONFIG),
        "scan",
        "dataset",
        "db",
        "postgresql+psycopg2://postgres:fidesctl@fidesctl-db:5432/fidesctl_test",
    )
    session.run(*run_command, external=True)


@nox.session()
def mypy(session: nox.Session) -> None:
    """Run the 'mypy' static type checker."""
    if session.posargs == ["docker"]:
        run_command = (*RUN_STATIC_ANALYSIS, "mypy")
    else:
        run_command = ("mypy",)
    session.run(*run_command, external=True)


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
