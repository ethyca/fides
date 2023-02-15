"""Contains the nox sessions for running development environments."""
from typing import Literal

from nox import Session, param, parametrize
from nox import session as nox_session
from nox.command import CommandFailed

from constants_nox import (
    COMPOSE_SERVICE_NAME,
    EXEC,
    RUN_CYPRESS_TESTS,
    START_APP,
    START_APP_REMOTE_DEBUG,
    START_TEST_ENV,
)
from docker_nox import build
from run_infrastructure import ALL_DATASTORES, run_infrastructure
from utils_nox import COMPOSE_DOWN_VOLUMES


@nox_session()
def dev(session: Session) -> None:
    """Spin up the application. Uses positional arguments for additional features."""

    build(session, "dev")
    session.notify("teardown")

    if "worker" in session.posargs:
        session.run("docker", "compose", "up", "--wait", "worker", external=True)

    datastores = [
        datastore for datastore in session.posargs if datastore in ALL_DATASTORES
    ] or None

    if "child" in session.posargs:
        session.run(
            "docker",
            "compose",
            "-f",
            "docker-compose.child-env.yml",
            "up",
            "-d",
            external=True,
        )

    if "ui" in session.posargs:
        build(session, "admin_ui")
        session.run("docker", "compose", "up", "-d", "fides-ui", external=True)

    if "pc" in session.posargs:
        build(session, "privacy_center")
        session.run("docker", "compose", "up", "-d", "fides-pc", external=True)

    open_shell = "shell" in session.posargs
    remote_debug = "remote_debug" in session.posargs
    if not datastores:
        if open_shell:
            session.run(*START_APP, external=True)
            session.run(*EXEC, "/bin/bash", external=True)
        else:
            if remote_debug:
                session.run(*START_APP_REMOTE_DEBUG, external=True)
            else:
                session.run(
                    "docker", "compose", "up", COMPOSE_SERVICE_NAME, external=True
                )
    else:
        # Run the webserver with additional datastores
        run_infrastructure(
            open_shell=open_shell,
            run_application=True,
            datastores=datastores,
            remote_debug=remote_debug,
        )


@nox_session()
def cypress_tests(session: Session) -> None:
    """
    End-to-end Cypress tests designed to be run as part of the 'e2e_test' session.
    """
    session.log("Running Cypress tests...")
    session.run(*RUN_CYPRESS_TESTS, external=True)


@nox_session()
def e2e_test(session: Session) -> None:
    """
    Spins up the test_env session and runs Cypress E2E tests against it.
    """
    session.log("Running end-to-end tests...")
    session.notify("fides_env(test)", posargs=["test"])
    session.notify("cypress_tests")
    session.notify("teardown")


@nox_session()
@parametrize(
    "fides_image",
    [
        param("dev", id="dev"),
        param("test", id="test"),
    ],
)
def fides_env(session: Session, fides_image: Literal["test", "dev"] = "test") -> None:
    """
    Spins up a full fides environment seeded with data.

    Params:
        dev = Spins up a full fides application with a dev-style docker container. This includes hot-reloading and no pre-baked UI.
        test = Spins up a full fides application with a production-style docker container. This includes the UI being pre-built as static files.

    Posargs:
        test = instead of running 'bin/bash', runs 'fides' to verify the CLI and provide a zero exit code
        keep_alive = does not automatically call teardown after the session
    """

    shell_command = "fides" if "test" in session.posargs else "/bin/bash"
    keep_alive = "keep_alive" in session.posargs

    # Temporarily override some ENV vars as needed. To set local secrets, see 'example.env'
    test_env_vars = {
        "FIDES__CONFIG_PATH": "/fides/src/fides/data/test_env/fides.test_env.toml",
    }

    session.log(
        "Tearing down existing containers & volumes to prepare test environment..."
    )
    try:
        session.run(*COMPOSE_DOWN_VOLUMES, external=True, env=test_env_vars)
    except CommandFailed:
        session.error(
            "Failed to cleanly teardown existing containers & volumes. Please exit out of all other and try again"
        )
    if not keep_alive:
        session.notify("teardown", posargs=["volumes"])

    session.log("Building images...")
    build(session, fides_image)
    build(session, "admin_ui")
    build(session, "privacy_center")

    session.log(
        "Starting the application with example databases defined in docker-compose.integration-tests.yml..."
    )
    session.run(
        *START_TEST_ENV, "fides-ui", "fides-pc", external=True, env=test_env_vars
    )

    session.log(
        "Running example setup scripts for DSR Automation tests... (scripts/load_examples.py)"
    )
    session.run(
        *EXEC,
        "python",
        "/fides/scripts/load_examples.py",
        external=True,
        env=test_env_vars,
    )

    session.log(
        "Pushing example resources for Data Mapping tests... (demo_resources/*)"
    )
    session.run(
        *EXEC,
        "fides",
        "push",
        "demo_resources/",
        external=True,
        env=test_env_vars,
    )

    # Make spaces in the info message line up
    title = (
        "FIDES TEST ENVIRONMENT" if fides_image == "test" else "FIDES DEV ENVIRONMENT "
    )

    session.log("****************************************")
    session.log("*                                      *")
    session.log(f"*        {title}        *")
    session.log("*                                      *")
    session.log("****************************************")
    session.log("")
    # Print out some helpful tips for using the test_env!
    # NOTE: These constants are defined in scripts/setup/constants.py, docker-compose.yml, and docker-compose.integration-tests.yml
    session.log(
        "Using secrets set in '.env' for example setup scripts (see 'example.env' for options)"
    )
    if fides_image == "test":
        session.log(
            "Fides Admin UI (production build) running at http://localhost:8080 (user: 'root_user', pass: 'Testpassword1!')"
        )
    session.log(
        "Fides Admin UI (dev) running at http://localhost:3000 (user: 'root_user', pass: 'Testpassword1!')"
    )
    session.log(
        "Fides Privacy Center (production build) running at http://localhost:3001 (user: 'jane@example.com')"
    )
    session.log(
        "Example Postgres Database running at localhost:6432 (user: 'postgres', pass: 'postgres', db: 'postgres_example')"
    )
    session.log(
        "Example Mongo Database running at localhost:27017 (user: 'mongo_test', pass: 'mongo_pass', db: 'mongo_test')"
    )
    session.log("Opening Fides CLI shell... (press CTRL+D to exit)")
    session.run(*EXEC, shell_command, external=True, env=test_env_vars)


@nox_session()
def quickstart(session: Session) -> None:
    """Run the quickstart tutorial."""
    build(session, "dev")
    build(session, "privacy_center")
    build(session, "admin_ui")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
