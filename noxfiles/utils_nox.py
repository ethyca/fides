"""Contains various utility-related nox sessions."""

from pathlib import Path

import nox

from constants_nox import COMPOSE_FILE_LIST, RUN
from run_infrastructure import run_infrastructure


@nox.session()
def seed_test_data(session: nox.Session) -> None:
    """Seed test data in the Postgres application database."""
    run_infrastructure(datastores=["postgres"], run_create_test_data=True)


@nox.session()
def clean(session: nox.Session) -> None:
    """
    Clean up docker containers, remove orphans, remove volumes
    and prune images related to this project.
    """
    teardown(session, volumes=True, images=True)
    session.run("docker", "system", "prune", "--force", "--all", external=True)
    print("Clean Complete!")


@nox.session()
def teardown(session: nox.Session, volumes: bool = False, images: bool = False) -> None:
    """Tear down all docker environments."""
    for compose_file in COMPOSE_FILE_LIST:
        teardown_command = (
            "docker",
            "compose",
            "-f",
            compose_file,
            "down",
            "--remove-orphans",
        )

        if volumes or "volumes" in session.posargs:
            teardown_command = (*teardown_command, "--volumes")

        if images:
            teardown_command = (*teardown_command, "--rmi", "all")

        try:
            session.run(*teardown_command, external=True)
        except nox.command.CommandFailed:
            session.warn(f"Teardown failed: '{teardown_command}'")

    session.log("Teardown complete")


def install_requirements(session: nox.Session, include_optional: bool = False) -> None:
    session.install("-r", "requirements.txt")
    session.install("-r", "dev-requirements.txt")
    if include_optional:
        session.install("-r", "optional-requirements.txt")


@nox.session()
def init_saas_connector(session: nox.Session) -> None:
    connector_name = session.posargs[0].replace(" ", "")
    connector_id = "_".join(session.posargs[0].lower().split(" "))
    variable_map = {"connector_name": connector_name, "connector_id": connector_id}

    # create empty config and dataset files
    try:
        Path(f"data/saas/config/{variable_map['connector_id']}_config.yml").touch(
            exist_ok=False
        )
        Path(f"data/saas/dataset/{variable_map['connector_id']}_dataset.yml").touch(
            exist_ok=False
        )
    except Exception:
        session.error(
            f"Files for {session.posargs[0]} already exist, skipping initialization"
        )

    # location of Jinja templates
    from jinja2 import Environment, FileSystemLoader

    environment = Environment(
        loader=FileSystemLoader("data/saas/saas_connector_scaffolding/")
    )

    # render fixtures file
    fixtures_template = environment.get_template("new_fixtures.jinja")
    filename = f"tests/fixtures/saas/{variable_map['connector_id']}_fixtures.py"
    contents = fixtures_template.render(variable_map)
    try:
        with open(filename, mode="x", encoding="utf-8") as fixtures:
            fixtures.write(contents)
            fixtures.close()
    except FileExistsError:
        session.error(
            f"Files for {session.posargs[0]} already exist, skipping initialization"
        )

    # render tests file
    test_template = environment.get_template("test_new_task.jinja")
    filename = (
        f"tests/ops/integration_tests/saas/test_{variable_map['connector_id']}_task.py"
    )
    contents = test_template.render(variable_map)
    try:
        with open(filename, mode="x", encoding="utf-8") as tests:
            tests.write(contents)
            tests.close()
    except FileExistsError:
        session.error(
            f"Files for {session.posargs[0]} already exist, skipping initialization"
        )


@nox.session()
@nox.parametrize(
    "db_command",
    [
        nox.param("init", id="init"),
        nox.param("reset", id="reset"),
    ],
)
def db(session: nox.Session, db_command: str) -> None:
    """Run commands against the database."""
    teardown(session)
    if db_command == "reset":
        reset_command = ("docker", "volume", "rm", "-f", "fides_app-db-data")
        session.run(*reset_command, external=True)
    init_command = (
        "python",
        "-c",
        "from fides.api.db.database import init_db; from fides.config import get_config; config = get_config(); init_db(config.database.sync_database_uri)",
    )
    session.run(*RUN, *init_command, external=True)
