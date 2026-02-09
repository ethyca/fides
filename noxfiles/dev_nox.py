"""Contains the nox sessions for running development environments."""

import hashlib
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Literal

from nox import Session, param, parametrize
from nox import session as nox_session
from nox.command import CommandFailed

from constants_nox import (
    COMPOSE_SERVICE_NAME,
    EXEC_IT,
    START_APP,
    START_APP_REMOTE_DEBUG,
)
from docker_nox import build
from run_infrastructure import ALL_DATASTORES, run_infrastructure
from utils_nox import install_requirements, teardown

# Default ports used by the dev environment
DEFAULT_PORTS = {
    "api": 8080,
    "db": 5432,
    "redis": 6379,
    "admin_ui": 3000,
    "privacy_center": 3001,
}


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def is_container_running(name: str) -> bool:
    """Check if a Docker container is running."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{name}$"],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def get_current_git_branch() -> str:
    """Get the current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def get_alternate_ports(branch: str) -> dict:
    """Calculate alternate ports based on branch name."""
    hash_val = int(hashlib.md5(branch.encode()).hexdigest()[:8], 16)
    base = 9000 + (hash_val % 50) * 100
    return {
        "api": base + 80,
        "db": base + 32,
        "redis": base + 79,
        "admin_ui": base,
        "privacy_center": base + 1,
    }


def get_container_suffix(branch: str) -> str:
    """Get container name suffix based on branch."""
    # Sanitize branch name for container naming
    sanitized = branch.replace("/", "-").replace("_", "-")
    return f"-{sanitized[:20]}"


def check_for_conflicts(session: Session) -> tuple[dict, str, str]:
    """
    Check if there's already a fides server running.
    Returns (ports_dict, container_suffix, image_suffix) to use.
    """
    # Check if the default API port is in use
    if not is_port_in_use(DEFAULT_PORTS["api"]):
        # No conflict, use defaults
        return DEFAULT_PORTS.copy(), "", ""

    # Port is in use - check if it's a fides or fidesplus container
    if is_container_running("fides") or is_container_running("fidesplus-slim"):
        # Another fides instance is running, use alternate ports
        branch = get_current_git_branch()
        alt_ports = get_alternate_ports(branch)
        suffix = get_container_suffix(branch)
        # Sanitize branch for image tag (lowercase, alphanumeric and hyphens only)
        image_suffix = "-" + branch.replace("/", "-").replace("_", "-").lower()[:20]

        session.log("")
        session.log("=" * 60)
        session.log(f"Existing fides server detected on port {DEFAULT_PORTS['api']}")
        session.log(
            f"Starting additional instance on alternate ports (branch: {branch})"
        )
        session.log(f"Will build with image suffix: {image_suffix}")
        session.log("=" * 60)
        session.log("")

        return alt_ports, suffix, image_suffix

    # Some other application is using the port
    session.error(
        f"Port {DEFAULT_PORTS['api']} is already in use by another application.\n"
        "Please free up the port or specify a different port configuration."
    )
    return DEFAULT_PORTS.copy(), "", ""  # Won't reach here due to error


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


# ruff: noqa: PLR0912
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
        - workers-all = Run all available Fides workers (see below)
        - flower = Run Flower monitoring dashboard for Celery
        - child = Run a Fides child node
        - nginx = Run two Fides webservers with nginx load balancer proxy
        - <datastore(s)> = Run a test datastore (e.g. 'mssql', 'mongodb')

    To run specific workers only, use any of the following posargs:
        - worker-dsr = Run a Fides DSR worker
        - worker-privacy-preferences = Run a Fides Privacy Preferences worker
        - worker-other = Run a Fides worker that excludes the dedicated queues

    Parameters:
        N/A
    """

    # Check for port conflicts with existing fides instances BEFORE building
    ports, container_suffix, image_suffix = check_for_conflicts(session)

    # Set IMAGE_SUFFIX env var for the build process
    if image_suffix:
        os.environ["IMAGE_SUFFIX"] = image_suffix

    # Build with the appropriate image tag
    build(session, "dev")
    session.notify("teardown")

    # Create environment variables for docker compose
    compose_env = {
        "API_PORT": str(ports["api"]),
        "DB_PORT": str(ports["db"]),
        "REDIS_PORT": str(ports["redis"]),
        "ADMIN_UI_PORT": str(ports["admin_ui"]),
        "PRIVACY_CENTER_PORT": str(ports["privacy_center"]),
        "CONTAINER_SUFFIX": container_suffix,
        "IMAGE_SUFFIX": image_suffix,
    }

    # Log the ports being used
    session.log("")
    session.log(f"  API:            http://localhost:{ports['api']}")
    if "ui" in session.posargs:
        session.log(f"  Admin UI:       http://localhost:{ports['admin_ui']}")
    if "pc" in session.posargs:
        session.log(f"  Privacy Center: http://localhost:{ports['privacy_center']}")
    session.log("")

    available_workers = ["worker-privacy-preferences", "worker-dsr", "worker-other"]
    workers = [
        worker
        for worker in available_workers
        if worker in session.posargs or "workers-all" in session.posargs
    ]
    for worker in workers:
        session.run(
            "docker", "compose", "up", "--wait", worker, external=True, env=compose_env
        )

    if "flower" in session.posargs:
        # Only start Flower if at least one worker is enabled
        if workers:
            session.run(
                "docker",
                "compose",
                "up",
                "-d",
                "flower",
                external=True,
                env=compose_env,
            )
        else:
            session.error(
                "Flower requires at least one worker service. Please add at least one 'worker' to your arguments."
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
            env=compose_env,
        )

    if "ui" in session.posargs:
        build(session, "admin_ui")
        session.run(
            "docker", "compose", "up", "-d", "fides-ui", external=True, env=compose_env
        )

    if "pc" in session.posargs:
        build(session, "privacy_center")
        session.run(
            "docker", "compose", "up", "-d", "fides-pc", external=True, env=compose_env
        )

    open_shell = "shell" in session.posargs
    remote_debug = "remote_debug" in session.posargs
    use_nginx = "nginx" in session.posargs

    if use_nginx:
        # Run two Fides webservers with nginx load balancer proxy
        session.run(
            "docker",
            "compose",
            "up",
            "fides-1",
            "fides-2",
            "fides-proxy",
            external=True,
            env=compose_env,
        )
    elif not datastores:
        if open_shell:
            session.run(*START_APP, external=True)
            session.log("~~Remember to login with `fides user login`!~~")
            session.run(*EXEC_IT, "/bin/bash", external=True)
        else:
            if remote_debug:
                session.run(*START_APP_REMOTE_DEBUG, external=True)
            else:
                session.run(
                    "docker",
                    "compose",
                    "up",
                    COMPOSE_SERVICE_NAME,
                    external=True,
                    env=compose_env,
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
            f"{index:5} | {value['label']:20} | {value['time'] - timestamps[index - 1]['time']:.2f}s"
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


@nox_session()
@parametrize(
    "action",
    [
        param("dry", id="dry"),
        param("live", id="live"),
    ],
)
def delete_old_test_pypi_packages(session: Session, action: str) -> None:
    """
    Delete old (specifically, >1 year old) packages from the test pypi repository.
    """
    session.install("pypi-cleanup")

    if action == "dry":
        session.run(
            "pypi-cleanup",
            "-u",
            "fides-ethyca",
            "-p",
            "ethyca-fides",
            "-t",
            "https://test.pypi.org",
            "-d",
            "365",
            "-y",
        )
    elif action == "live":
        session.run(
            "pypi-cleanup",
            "-u",
            "fides-ethyca",
            "-p",
            "ethyca-fides",
            "-t",
            "https://test.pypi.org",
            "-d",
            "365",
            "-y",
            "--do-it",
        )
