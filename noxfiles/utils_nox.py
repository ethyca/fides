"""Contains various utility-related nox sessions."""
import nox

from constants_nox import COMPOSE_FILE, INTEGRATION_COMPOSE_FILE, TEST_ENV_COMPOSE_FILE
from run_infrastructure import run_infrastructure

COMPOSE_DOWN = (
    "docker",
    "compose",
    "-f",
    COMPOSE_FILE,
    "-f",
    INTEGRATION_COMPOSE_FILE,
    "-f",
    TEST_ENV_COMPOSE_FILE,
    "-f",
    "docker/docker-compose.integration-mariadb.yml",
    "-f",
    "docker/docker-compose.integration-mongodb.yml",
    "-f",
    "docker/docker-compose.integration-mysql.yml",
    "-f",
    "docker/docker-compose.integration-postgres.yml",
    "-f",
    "docker/docker-compose.integration-mssql.yml",
    "down",
    "--remove-orphans",
)
COMPOSE_DOWN_VOLUMES = COMPOSE_DOWN + ("--volumes",)


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
    clean_command = (*COMPOSE_DOWN, "--volumes", "--rmi", "all")
    session.run(*clean_command, external=True)
    session.run("docker", "system", "prune", "--force", "--all", external=True)
    print("Clean Complete!")


@nox.session()
def teardown(session: nox.Session) -> None:
    """Tear down the docker dev environment."""
    if "volumes" in session.posargs:
        session.run(*COMPOSE_DOWN_VOLUMES, external=True)
    else:
        session.run(*COMPOSE_DOWN, external=True)
    print("Teardown complete")


def install_requirements(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")
    session.install("-r", "dev-requirements.txt")


@nox.session()
def init_saas_connector(session: nox.Session) -> None:
    connector_name = session.posargs[0].replace(" ", "")
    connector_id = "_".join(session.posargs[0].lower().split(" "))
    variable_map = {"connector_name": connector_name, "connector_id": connector_id}

    # create empty config and dataset files
    try:
        open(f"data/saas/config/{variable_map['connector_id']}_config.yml", "x")
        open(f"data/saas/dataset/{variable_map['connector_id']}_dataset.yml", "x")
    except FileExistsError:
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
    with open(filename, mode="w", encoding="utf-8") as fixtures:
        fixtures.write(contents)
        fixtures.close()

    # render tests file
    test_template = environment.get_template("test_new_task.jinja")
    filename = (
        f"tests/ops/integration_tests/saas/test_{variable_map['connector_id']}_task.py"
    )
    contents = test_template.render(variable_map)
    with open(filename, mode="w", encoding="utf-8") as tests:
        tests.write(contents)
        tests.close()
