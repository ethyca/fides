"""Contains the nox sessions for running development environments."""
import nox

from constants_nox import COMPOSE_SERVICE_NAME, RUN, START_APP
from docker_nox import build
from run_infrastructure import ALL_DATASTORES, run_infrastructure


@nox.session()
def dev(session: nox.Session) -> None:
    """Spin up the application. Uses positional arguments for additional features."""
    build(session, "dev")
    session.notify("teardown")

    datastores = [
        datastore for datastore in session.posargs if datastore in ALL_DATASTORES
    ] or None

    if "ui" in session.posargs:
        build(session, "ui")
        session.run("docker", "compose", "up", "-d", "fides-ui", external=True)

    if "pc" in session.posargs:
        build(session, "pc")
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


@nox.session()
def quickstart(session: nox.Session) -> None:
    """Run the quickstart tutorial."""
    build(session, "dev")
    session.notify("teardown")
    run_infrastructure(datastores=["mongodb", "postgres"], run_quickstart=True)


@nox.session()
@nox.parametrize(
    "script_name",
    [
        nox.param("example_script", id="example_script"),
    ],
)
def run_script(session: nox.Session, script_name: str) -> None:
    """
    Run a script from the scripts/ directory. This command will not run
    the server automatically.
    """
    posargs = session._runner.posargs
    posargs.remove(script_name)
    session.run(
        "docker",
        "compose",
        "run",
        *posargs,
        COMPOSE_SERVICE_NAME,
        "python",
        f"/fides/scripts/{script_name}.py",
        external=True,
    )
