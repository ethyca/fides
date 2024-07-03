"""Contains the nox sessions for developing docs."""

import nox
from constants_nox import CI_ARGS


@nox.session()
def generate_docs(session: nox.Session) -> None:
    """Check that the autogenerated docs build succeeds."""
    session.install(".")
    session.run("python", "scripts/generate_docs.py")


@nox.session()
def docs_serve(session: nox.Session) -> None:
    """Serve the docs."""
    generate_docs(session)
    session.notify("teardown")
    session.run("docker", "compose", "build", "docs", external=True)
    run_shell = (
        "docker",
        "compose",
        "run",
        "--rm",
        "--service-ports",
        CI_ARGS,
        "docs",
        "/bin/bash",
        "-c",
        "mkdocs serve --dev-addr=0.0.0.0:8000",
    )
    session.run(*run_shell, external=True)


@nox.session()
def docs_check(session: nox.Session) -> None:
    """Check that the docs can build."""
    generate_docs(session)
    session.notify("teardown")
    session.run("docker", "compose", "build", "docs", external=True)
    run_shell = (
        "docker",
        "compose",
        "run",
        "--rm",
        "--service-ports",
        CI_ARGS,
        "docs",
        "/bin/bash",
        "-c",
        "pip install -e /fides && mkdocs build",
    )
    session.run(*run_shell, external=True)
