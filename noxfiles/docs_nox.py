"""Contains the nox sessions for developing docs."""
import nox
from constants_nox import CI_ARGS, RUN
from docker_nox import build_local


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
