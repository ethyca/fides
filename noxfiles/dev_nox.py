"""Contains the nox sessions for running development environments."""
from pathlib import Path
from typing import Literal

from constants_nox import (
    COMPOSE_SERVICE_NAME,
    EXEC_IT,
    RUN_CYPRESS_TESTS,
    START_APP,
    START_APP_REMOTE_DEBUG,
)
from docker_nox import build
from nox import Session, param, parametrize
from nox import session as nox_session
from nox.command import CommandFailed
from run_infrastructure import ALL_DATASTORES, run_infrastructure
from utils_nox import teardown


@nox_session()
def shell(session: Session) -> None:
    """
    Open a shell in an already-running Fides webserver container.

    If the container is not running, the command will fail.
    """
    shell_command = (*EXEC_IT, "/bin/bash")
    try:
        session.run(*shell_command, external=True)
    except CommandFailed:
        session.error(
            "Could not connect to the webserver container. Please confirm it is running and try again."
        )


@nox_session()
def dev(session: Session) -> None:
    """
    Spin up the Fides webserver in development mode alongside it's Postgres
    database and Redis cache. Use positional arguments to run other services
    like privacy center, shell, admin UI, etc. (see usage for examples)

    Usage:
      'nox -s dev' - runs the Fides weserver, database, and cache
      'nox -s dev -- shell' - also open a shell on the Fides webserver
      'nox -s dev -- ui' - also build and run the Admin UI
      'nox -s dev -- pc' - also build and run the Privacy Center
      'nox -s dev -- remote_debug' - run with remote debugging enabled (see docker-compose.remote-debug.yml)
      'nox -s dev -- worker' - also run a Fides worker
      'nox -s dev -- child' - also run a Fides child node
      'nox -s dev -- <datastore>' - also run a test datastore (e.g. 'mssql', 'mongodb')

    Note that you can combine any of the above arguments together, for example:
      'nox -s dev -- shell ui pc'

    See noxfiles/dev_nox.py for more info
    """

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
            session.log("~~Remember to login with `fides user login`!~~")
            session.run(*EXEC_IT, "/bin/bash", external=True)
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
    Spins up the fides_env session and runs Cypress E2E tests against it.
    """
    session.log("Running end-to-end tests...")
    session.notify("fides_env(test)", posargs=["keep_alive"])
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
        keep_alive = does not automatically call teardown after the session
    """

    keep_alive = "keep_alive" in session.posargs

    session.log("Tearing down existing containers & volumes...")
    try:
        teardown(session)
    except CommandFailed:
        session.error("Failed to cleanly teardown. Please try again!")

    session.log("Building production images with 'build(test)'...")
    build(session, "test")

    session.log("Installing ethyca-fides locally...")
    session.run("pip", "install", ".")
    session.run("fides", "--version")

    # Configure the args for 'fides deploy up' for testing
    env_file_path = Path(__file__, "../../.env").resolve()
    fides_deploy_args = [
        "--no-pull",
        "--no-init",
        "--env-file",
        str(env_file_path),
    ]
    if fides_image == "dev":
        session.log("Enabling hot-reloading by running uvicorn directly...")
        fides_deploy_args.extend(
            [
                "--command",
                "uvicorn --reload --reload-dir src fides.api.main:app",
            ]
        )

    session.log("Deploying test environment with 'fides deploy up'...")
    session.log(
        f"NOTE: Customize your local Fides configuration via ENV file here: {env_file_path}"
    )
    session.run(
        "fides",
        "deploy",
        "up",
        *fides_deploy_args,
    )
    if not keep_alive:
        session.log("Opening Fides CLI shell... (press CTRL+D to exit)")
        session.run(*EXEC_IT, "/bin/bash", external=True, success_codes=[0, 1])
        session.run("fides", "deploy", "down")


@nox_session()
def quickstart(session: Session) -> None:
    """Run the quickstart tutorial."""
    build(session, "dev")
    build(session, "privacy_center")
    build(session, "admin_ui")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)
