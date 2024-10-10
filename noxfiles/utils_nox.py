"""Contains various utility-related nox sessions."""

from pathlib import Path

import nox
import yaml

from constants_nox import COMPOSE_FILE_LIST
from run_infrastructure import run_infrastructure
from loguru import logger

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

    config_path = Path(f"data/saas/config/{variable_map['connector_id']}_config.yml")
    dataset_path = Path(f"data/saas/dataset/{variable_map['connector_id']}_dataset.yml")

    try:
        config_path.touch(exist_ok=False)
        dataset_path.touch(exist_ok=False)
    except Exception:
        logger.warning(
            f"Files for {session.posargs[0]} already exist, skipping config and dataset files"
        )

    # location of Jinja templates
    from jinja2 import Environment, FileSystemLoader

    environment = Environment(
        loader=FileSystemLoader("data/saas/saas_connector_scaffolding/")
    )

    # render fixtures file
    fixtures_template = environment.get_template("new_fixtures.jinja")
    filename = f"tests/fixtures/saas/{variable_map['connector_id']}_fixtures.py"

    if config_path.exists and dataset_path.exists:
        config = yaml.safe_load(config_path.open('r'))
    integration = config["saas_config"]

    # check if external references is present
    external = True if "external_references" in integration.keys() else False

    # extract the type of request
    requests = [endpoint["requests"] for endpoint in integration["endpoints"]]
    method = [request.keys() for request in requests]
    keys = [list(key)[0] for key in method]

    variable_map["external"] = external
    variable_map["methods"] = keys
    variable_map["delete"] = False
    variable_map["read"] = False

    if any(key in ["update", "delete"] for key in keys):
        variable_map["delete"] = True
    if any(key == "read" for key in keys):
        variable_map["read"] = True

    contents = fixtures_template.render(variable_map)
    try:
        with open(filename, mode="x", encoding="utf-8") as fixtures:
            fixtures.write(contents)
            fixtures.close()
    except FileExistsError:
        session.error(
            f"Files for {session.posargs[0]} already exist, skipping initialization"
        )

    # # render tests file
    # test_template = environment.get_template("test_new_task.jinja")
    # filename = (
    #     f"tests/ops/integration_tests/saas/test_{variable_map['connector_id']}_task.py"
    # )
    # contents = test_template.render(variable_map)
    # try:
    #     with open(filename, mode="x", encoding="utf-8") as tests:
    #         tests.write(contents)
    #         tests.close()
    # except FileExistsError:
    #     session.error(
    #         f"Files for {session.posargs[0]} already exist, skipping initialization"
    #     )
