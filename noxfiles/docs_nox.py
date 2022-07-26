"""Contains the nox sessions for developing docs."""
import nox
from constants_nox import CI_ARGS, RUN
from docker_nox import build


@nox.session()
@nox.parametrize(
    "build_type", [nox.param("local", id="local"), nox.param("ci", id="ci")]
)
def docs_build(session: nox.Session, build_type: str) -> None:
    """Build docs from the source code."""
    session.notify("teardown")
    if build_type == "local":
        build(session, "dev")
    run_shell = (
        *RUN,
        "python",
        "scripts/generate_openapi.py",
        "docs/fidesops/docs/api/openapi.json",
    )
    session.run(*run_shell, external=True)


@nox.session()
def docs_serve(session: nox.Session) -> None:
    """Serve the docs."""
    docs_build(session, "local")
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
        "mkdocs serve --dev-addr=0.0.0.0:8000",
    )
    session.run(*run_shell, external=True)


@nox.session()
def docs_check(session: nox.Session) -> None:
    """Check that the docs can build."""
    docs_build(session, "ci")
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
        "mkdocs build",
    )
    session.run(*run_shell, external=True)
