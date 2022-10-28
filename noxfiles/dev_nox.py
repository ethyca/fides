"""Contains the nox sessions for running development environments."""
from nox import Session
from nox import session as nox_session
from nox.command import CommandFailed

from constants_nox import (
    COMPOSE_SERVICE_NAME,
    RUN,
    RUN_NO_DEPS,
    START_APP,
    START_APP_EXTERNAL,
)
from docker_nox import build
from run_infrastructure import ALL_DATASTORES, run_infrastructure
from utils_nox import COMPOSE_DOWN_VOLUMES


@nox_session()
def dev(session: Session) -> None:
    """Spin up the application. Uses positional arguments for additional features."""

    build(session, "dev")
    session.notify("teardown")

    datastores = [
        datastore for datastore in session.posargs if datastore in ALL_DATASTORES
    ] or None

    if "ui" in session.posargs:
        build(session, "admin_ui")
        session.run("docker", "compose", "up", "-d", "fides-ui", external=True)

    if "pc" in session.posargs:
        build(session, "privacy_center")
        session.run("docker", "compose", "up", "-d", "fides-pc", external=True)

    open_shell = "shell" in session.posargs
    if not datastores:
        if open_shell:
            session.run(*START_APP, external=True)
            session.run(*RUN, "/bin/bash", external=True)
        else:
            session.run("docker", "compose", "up", COMPOSE_SERVICE_NAME, external=True)
    else:
        # Run the webserver with additional datastores
        run_infrastructure(
            open_shell=open_shell, run_application=True, datastores=datastores
        )


@nox_session()
def test_env(session: Session) -> None:
    """
    Spins up a comprehensive test environment seeded with data.

    Posargs:
    test: instead of running 'bin/bash', runs 'fides' to verify the CLI and provide a zero exit code
    """

    shell_command = "fides" if "test" in session.posargs else "/bin/bash"

    # Temporarily override some ENV vars as needed. To set local secrets, see 'example.env'
    test_env_vars = {
        "FIDES__CONFIG_PATH": "/fides/data/config/fides.test_env.toml",
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
    session.notify("teardown", posargs=["volumes"])

    session.log("Building images...")
    build(session, "dev")
    build(session, "admin_ui")
    build(session, "privacy_center")

    session.log(
        "Starting the application with example databases defined in docker-compose.integration-tests.yml..."
    )
    session.run(
        *START_APP_EXTERNAL, "fides-ui", "fides-pc", external=True, env=test_env_vars
    )

    session.log(
        "Running example setup scripts for DSR Automation tests... (scripts/load_examples.py)"
    )
    session.run(
        *RUN_NO_DEPS,
        "python",
        "/fides/scripts/load_examples.py",
        external=True,
        env=test_env_vars,
    )

    session.log(
        "Pushing example resources for Data Mapping tests... (demo_resources/*)"
    )
    session.run(
        *RUN_NO_DEPS,
        "fides",
        "push",
        "demo_resources/",
        external=True,
        env=test_env_vars,
    )

    session.log("****************************************")
    session.log("*                                      *")
    session.log("*        FIDES TEST ENVIRONMENT        *")
    session.log("*                                      *")
    session.log("****************************************")
    session.log("")
    # Print out some helpful tips for using the test_env!
    # NOTE: These constants are defined in scripts/setup/constants.py, docker-compose.yml, and docker-compose.integration-tests.yml
    session.log(
        "Using secrets set in '.env' for example setup scripts (see 'example.env' for options)"
    )
    session.log(
        "Fides Admin UI running at http://localhost:3000 (user: 'fidesuser', pass: 'Apassword1!')"
    )
    session.log(
        "Fides Privacy Center running at http://localhost:3001 (user: 'jane@example.com')"
    )
    session.log(
        "Example Postgres Database running at localhost:6432 (user: 'postgres', pass: 'postgres', db: 'postgres_example')"
    )
    session.log(
        "Example Mongo Database running at localhost:27017 (user: 'mongo_test', pass: 'mongo_pass', db: 'mongo_test')"
    )
    session.log("Opening Fides CLI shell... (press CTRL+D to exit)")
    session.run(*RUN_NO_DEPS, shell_command, external=True, env=test_env_vars)


@nox_session()
def quickstart(session: Session) -> None:
    """Run the quickstart tutorial."""
    build(session, "dev")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
