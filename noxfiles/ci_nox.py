"""Contains the nox sessions used during CI checks."""

from functools import partial
from typing import Callable, Dict

import nox
from nox.command import CommandFailed

from constants_nox import (
    CONTAINER_NAME,
    IMAGE_NAME,
    LOGIN,
    RUN_NO_DEPS,
    START_APP,
    WITH_TEST_CONFIG,
)
from setup_tests_nox import pytest_ctl, pytest_lib, pytest_nox, pytest_ops
from utils_nox import install_requirements


###################
## Static Checks ##
###################
@nox.session()
def static_checks(session: nox.Session) -> None:
    """Run the static checks only."""
    session.notify("black(fix)")
    session.notify("isort(fix)")
    session.notify("xenon")
    session.notify("mypy")
    session.notify("pylint")


@nox.session()
@nox.parametrize(
    "mode",
    [
        nox.param("check", id="check"),
        nox.param("fix", id="fix"),
    ],
)
def black(session: nox.Session, mode: str) -> None:
    """Run the 'black' style linter."""
    install_requirements(session)
    command = ("black", "src", "tests", "noxfiles", "scripts", "noxfile.py")
    if session.posargs:
        command = ("black", *session.posargs)
    if mode == "check":
        command = (*command, "--check")
    session.run(*command)


@nox.session()
@nox.parametrize(
    "mode",
    [
        nox.param("check", id="check"),
        nox.param("fix", id="fix"),
    ],
)
def isort(session: nox.Session, mode: str) -> None:
    """Run the 'isort' import linter."""
    install_requirements(session)
    command = ("isort", "src", "tests", "noxfiles", "scripts", "noxfile.py")
    if session.posargs:
        command = ("isort", *session.posargs)
    if mode == "check":
        command = (*command, "--check")
    session.run(*command)


@nox.session()
def mypy(session: nox.Session) -> None:
    """Run the 'mypy' static type checker."""
    install_requirements(session)
    command = "mypy"
    session.run(command)


@nox.session()
def pylint(session: nox.Session) -> None:
    """Run the 'pylint' code linter."""
    install_requirements(session)
    command = ("pylint", "src", "noxfiles", "noxfile.py", "--jobs", "0")
    session.run(*command)


@nox.session()
def xenon(session: nox.Session) -> None:
    """Run 'xenon' code complexity monitoring."""
    install_requirements(session)
    command = (
        "xenon",
        "noxfiles",
        "src",
        "tests",
        "scripts",
        "--max-absolute=B",
        "--max-modules=B",
        "--max-average=A",
        "--ignore=data,docs",
        "--exclude=src/fides/_version.py",
    )
    session.run(*command, success_codes=[0, 1])
    session.log(
        "Note: This command was malformed so it's been failing to report complexity issues."
    )
    session.log(
        "Intentionally suppressing the error status code for now to slowly work through the issues."
    )


##################
## Fides Checks ##
##################
@nox.session()
def check_install(session: nox.Session) -> None:
    """
    Check that fides installs and works correctly.

    This is also a good sanity check for correct syntax.
    """
    session.install(".")

    REQUIRED_ENV_VARS = {
        "FIDES__SECURITY__APP_ENCRYPTION_KEY": "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3",
        "FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID": "fidesadmin",
        "FIDES__SECURITY__OAUTH_ROOT_CLIENT_SECRET": "fidesadminsecret",
        "FIDES__SECURITY__DRP_JWT_SECRET": "secret",
    }

    run_command = ("fides", "--version")
    session.run(*run_command, env=REQUIRED_ENV_VARS)

    run_command = ("python", "-c", "from fides.api.main import start_webserver")
    session.run(*run_command, env=REQUIRED_ENV_VARS)


@nox.session()
def check_fides_annotations(session: nox.Session) -> None:
    """Run a fides evaluation."""
    run_command = (*RUN_NO_DEPS, "fides", "--local", *(WITH_TEST_CONFIG), "evaluate")
    session.run(*run_command, external=True)


@nox.session()
def fides_db_scan(session: nox.Session) -> None:
    """Scan the fides application database to check for dataset discrepancies."""
    session.notify("teardown")
    session.run(*START_APP, external=True)
    scan_command = (
        "docker",
        "container",
        "exec",
        CONTAINER_NAME,
        "fides",
        "scan",
        "dataset",
        "db",
        "--credentials-id",
        "app_postgres",
    )
    session.run(*LOGIN, external=True)
    session.run(*scan_command, external=True)


@nox.session()
def check_container_startup(session: nox.Session) -> None:
    """
    Start the containers in `wait` mode. If container startup fails, show logs.
    """
    throw_error = False
    start_command = (
        "docker",
        "compose",
        "up",
        "--wait",
        IMAGE_NAME,
    )
    healthcheck_logs_command = (
        "docker",
        "inspect",
        "--format",
        '"{{json .State.Health }}"',
        IMAGE_NAME,
    )
    startup_logs_command = (
        "docker",
        "logs",
        "--tail",
        "50",
        IMAGE_NAME,
    )
    try:
        session.run(*start_command, external=True)
    except CommandFailed:
        throw_error = True

    # We want to see the logs regardless of pass/failure, just in case
    log_dashes = "*" * 20
    session.log(f"{log_dashes} Healthcheck Logs {log_dashes}")
    session.run(*healthcheck_logs_command, external=True)
    session.log(f"{log_dashes} Startup Logs {log_dashes}")
    session.run(*startup_logs_command, external=True)

    if throw_error:
        session.error("Container startup failed")


@nox.session()
def minimal_config_startup(session: nox.Session) -> None:
    """
    Check that the server can start successfully with a minimal
    configuration set through environment vairables.
    """
    session.notify("teardown")
    compose_file = "docker/docker-compose.minimal-config.yml"
    start_command = (
        "docker",
        "compose",
        "-f",
        compose_file,
        "up",
        "--wait",
        IMAGE_NAME,
    )
    session.run(*start_command, external=True)


#################
## Performance ##
#################
@nox.session()
def performance_tests(session: nox.Session) -> None:
    """Compose the various performance checks into a single uber-test."""
    session.notify("teardown")
    session.run(*START_APP, external=True, silent=True)
    samples = 2
    for i in range(samples):
        session.log(f"Sample {i + 1} of {samples}")
        load_tests(session)
        docker_stats(session)


@nox.session()
def docker_stats(session: nox.Session) -> None:
    """
    Use the builtin `docker stats` command to show resource usage.

    Run this _last_ to get a better worst-case scenario
    """
    session.run(
        "docker",
        "stats",
        "--no-stream",
        "--format",
        "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}",
        external=True,
    )


@nox.session()
def load_tests(session: nox.Session) -> None:
    """
    Load test the application.

    Requires a Rust/Cargo installation and then `cargo install drill`

    https://github.com/fcsonline/drill
    """
    session.run(
        "drill", "-b", "noxfiles/drill.yml", "--quiet", "--stats", external=True
    )


############
## Pytest ##
############
TEST_GROUPS = [
    nox.param("ctl-unit", id="ctl-unit"),
    nox.param("ctl-not-external", id="ctl-not-external"),
    nox.param("ctl-integration", id="ctl-integration"),
    nox.param("ctl-external", id="ctl-external"),
    nox.param("ops-unit", id="ops-unit"),
    nox.param("ops-unit-api", id="ops-unit-api"),
    nox.param("ops-unit-non-api", id="ops-unit-non-api"),
    nox.param("ops-integration", id="ops-integration"),
    nox.param("ops-external-datastores", id="ops-external-datastores"),
    nox.param("ops-saas", id="ops-saas"),
    nox.param("lib", id="lib"),
    nox.param("nox", id="nox"),
]

TEST_MATRIX: Dict[str, Callable] = {
    "ctl-unit": partial(pytest_ctl, mark="unit"),
    "ctl-not-external": partial(pytest_ctl, mark="not external"),
    "ctl-integration": partial(pytest_ctl, mark="integration"),
    "ctl-external": partial(pytest_ctl, mark="external"),
    "ops-unit": partial(pytest_ops, mark="unit"),
    "ops-unit-api": partial(pytest_ops, mark="unit", subset_dir="api"),
    "ops-unit-non-api": partial(pytest_ops, mark="unit", subset_dir="non-api"),
    "ops-integration": partial(pytest_ops, mark="integration"),
    "ops-external-datastores": partial(pytest_ops, mark="external_datastores"),
    "ops-saas": partial(pytest_ops, mark="saas"),
    "lib": pytest_lib,
    "nox": pytest_nox,
}


def validate_test_matrix(session: nox.Session) -> None:
    """
    Validates that all test groups are represented in the test matrix.
    """
    test_group_ids = sorted([str(param) for param in TEST_GROUPS])
    test_matrix_keys = sorted(TEST_MATRIX.keys())

    if not test_group_ids == test_matrix_keys:
        session.error("TEST_GROUPS and TEST_MATRIX do not match")


@nox.session()
def collect_tests(session: nox.Session) -> None:
    """
    Collect all pytests as a validity check.

    Good to run as a sanity check that there aren't any obvious syntax
    errors within the test code.
    """
    session.install(".")
    install_requirements(session, True)
    command = ("pytest", "tests/", "--collect-only")
    session.run(*command)


@nox.session()
@nox.parametrize(
    "test_group",
    TEST_GROUPS,
)
def pytest(session: nox.Session, test_group: str) -> None:
    """
    Runs Pytests.

    As new TEST_GROUPS are added, the TEST_MATRIX must also be updated.
    """
    session.notify("teardown")

    validate_test_matrix(session)
    coverage_arg = "--cov-report=xml"
    TEST_MATRIX[test_group](session=session, coverage_arg=coverage_arg)


@nox.session()
@nox.parametrize(
    "dist",
    [
        nox.param("sdist", id="source"),
        nox.param("bdist_wheel", id="wheel"),
    ],
)
def python_build(session: nox.Session, dist: str) -> None:
    "Build the Python distribution."
    session.run(
        *RUN_NO_DEPS,
        "python",
        "setup.py",
        dist,
        external=True,
    )
