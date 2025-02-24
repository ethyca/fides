"""Contains the nox sessions for running development environments."""

import time
from pathlib import Path
from typing import Literal

from nox import Session, param, parametrize
from nox import session as nox_session
from nox.command import CommandFailed

from constants_nox import (
    COMPOSE_SERVICE_NAME,
    EXEC_IT,
    RUN_CYPRESS_TESTS,
    START_APP,
    START_APP_REMOTE_DEBUG,
)
from docker_nox import build
from run_infrastructure import ALL_DATASTORES, run_infrastructure
from utils_nox import install_requirements, teardown


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


# pylint: disable=too-many-branches
@nox_session()
def dev(session: Session) -> None:
    """
    Spin up the Fides webserver in development mode.
    Includes the Postgres database and Redis cache.

    Use positional arguments to run other services like the privacy center & admin UI.
    Positional arguments can be combined and in any order.

    Positional Arguments:
        - shell = Open a shell on the Fides webserver
        - ui = Build and run the Admin UI
        - pc = Build and run the Privacy Center
        - remote_debug = Run with remote debugging enabled (see docker-compose.remote-debug.yml)
        - worker = Run a Fides worker
        - flower = Run Flower monitoring dashboard for Celery
        - child = Run a Fides child node
        - <datastore(s)> = Run a test datastore (e.g. 'mssql', 'mongodb')

    Parameters:
        N/A
    """

    build(session, "dev")
    session.notify("teardown")

    if "worker" in session.posargs:
        session.run("docker", "compose", "up", "--wait", "worker", external=True)

    if "worker-privacy-preferences" in session.posargs:
        session.run(
            "docker",
            "compose",
            "up",
            "--wait",
            "worker-privacy-preferences",
            external=True,
        )

    if "worker-dsr" in session.posargs:
        session.run("docker", "compose", "up", "--wait", "worker-dsr", external=True)

    if "flower" in session.posargs:
        # Only start Flower if worker is also enabled
        if "worker" in session.posargs:
            session.run("docker", "compose", "up", "-d", "flower", external=True)
        else:
            session.error(
                "Flower requires the worker service. Please add 'worker' to your arguments."
            )

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
        dev = Spins up a full fides application with a dev-style docker container.
              This includes hot-reloading and no pre-baked UI.

        test = Spins up a full fides application with a production-style docker
               container. This includes the UI being pre-built as static files.

    Posargs:
        keep_alive = does not automatically call teardown after the session
    """
    keep_alive = "keep_alive" in session.posargs
    if fides_image == "dev":
        session.error(
            "'fides_env(dev)' is not currently implemented! Use 'nox -s dev' to run the server in dev mode. "
            "Currently unclear how to (cleanly) mount the source code into the running container..."
        )

    # Record timestamps along the way, so we can generate a build-time report
    timestamps = []
    timestamps.append({"time": time.monotonic(), "label": "Start"})

    session.log("Tearing down existing containers & volumes...")
    try:
        teardown(session, volumes=True)
    except CommandFailed:
        session.error("Failed to cleanly teardown. Please try again!")
    timestamps.append({"time": time.monotonic(), "label": "Docker Teardown"})

    session.log("Building production images with 'build(test)'...")
    build(session, "test")
    timestamps.append({"time": time.monotonic(), "label": "Docker Build"})

    session.log("Installing ethyca-fides locally...")
    install_requirements(session)
    session.install("-e", ".", "--no-deps")
    session.run("fides", "--version")
    timestamps.append({"time": time.monotonic(), "label": "pip install"})

    # Configure the args for 'fides deploy up' for testing
    env_file_path = Path(__file__, "../../.env").resolve()
    fides_deploy_args = [
        "--no-pull",
        "--no-init",
        "--env-file",
        str(env_file_path),
    ]

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
    timestamps.append({"time": time.monotonic(), "label": "fides deploy"})

    # Log a quick build-time report to help troubleshoot slow builds
    session.log("[fides_env]: Ready! Build time report:")
    session.log(f"{'Step':5} | {'Label':20} | Time")
    session.log("------+----------------------+------")
    for index, value in enumerate(timestamps):
        if index == 0:
            continue
        session.log(
            f"{index:5} | {value['label']:20} | {value['time'] - timestamps[index-1]['time']:.2f}s"
        )
    session.log(
        f"      | {'Total':20} | {timestamps[-1]['time'] - timestamps[0]['time']:.2f}s"
    )
    session.log("------+----------------------+------\n")

    # Start a shell session unless 'keep_alive' is provided as a posarg
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
