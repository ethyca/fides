"""
This file invokes a command used to setup infrastructure for use in testing Fidesops
and related workflows.
"""
# pylint: disable=inconsistent-return-statements
import argparse
import subprocess
import sys
from time import sleep
from typing import List

from constants_nox import COMPOSE_SERVICE_NAME

DOCKER_WAIT = 5
DOCKERFILE_DATASTORES = [
    "mssql",
    "postgres",
    "mysql",
    "mongodb",
    "mariadb",
    "timescale",
]
EXTERNAL_DATASTORE_CONFIG = {
    "snowflake": ["SNOWFLAKE_TEST_URI"],
    "redshift": ["REDSHIFT_TEST_URI", "REDSHIFT_TEST_DB_SCHEMA"],
    "bigquery": ["BIGQUERY_KEYFILE_CREDS", "BIGQUERY_DATASET"],
}
EXTERNAL_DATASTORES = list(EXTERNAL_DATASTORE_CONFIG.keys())
ALL_DATASTORES = DOCKERFILE_DATASTORES + EXTERNAL_DATASTORES
OPS_TEST_DIR = "tests/ops/"


def run_infrastructure(
    datastores: List[str] = [],  # Which infra should we create? If empty, we create all
    open_shell: bool = False,  # Should we open a bash shell?
    pytest_path: str = "",  # Which subset of tests should we run?
    run_application: bool = False,  # Should we run the Fidesops webserver?
    run_quickstart: bool = False,  # Should we run the quickstart command?
    run_tests: bool = False,  # Should we run the tests after creating the infra?
    run_create_test_data: bool = False,  # Should we run the create_test_data command?
    analytics_opt_out: bool = False,  # Should we opt out of analytics?
) -> None:
    """
    - Create a Docker Compose file path for all datastores specified in `datastores`.
    - Defaults to creating infrastructure for all datastores in `DOCKERFILE_DATASTORES` if none
    are provided.
    - Optionally runs integration tests against those datastores from the container identified
    with `COMPOSE_SERVICE_NAME`.
    """

    if len(datastores) == 0:
        _run_cmd_or_err(
            'echo "no datastores specified, configuring infrastructure for all datastores"'
        )
        datastores = DOCKERFILE_DATASTORES + EXTERNAL_DATASTORES
    else:
        _run_cmd_or_err(f'echo "datastores specified: {", ".join(datastores)}"')

    # De-duplicate datastores
    datastores = list(set(datastores))

    # Configure docker-compose path
    path: str = get_path_for_datastores(datastores)

    _run_cmd_or_err(f'echo "infrastructure path: {path}"')
    if "mssql" not in datastores:
        _run_cmd_or_err(
            f'docker-compose {path} build --build-arg SKIP_MSSQL_INSTALLATION="true"'
        )
    else:
        _run_cmd_or_err(f"docker-compose {path} build")

    _run_cmd_or_err(f"docker-compose {path} up -d")

    wait = min(DOCKER_WAIT * len(datastores), 15)
    print(f"Sleeping for: {wait} while infrastructure loads...")
    sleep(wait)

    seed_initial_data(
        datastores,
        path,
        service_name=COMPOSE_SERVICE_NAME,
    )

    if open_shell:
        return _open_shell(path, COMPOSE_SERVICE_NAME)

    if run_application:
        return _run_application(path)

    if run_quickstart:
        return _run_quickstart(path, COMPOSE_SERVICE_NAME)

    if run_tests:
        # Now run the tests
        return _run_tests(
            datastores,
            docker_compose_path=path,
            pytest_path=pytest_path,
            analytics_opt_out=analytics_opt_out,
        )

    if run_create_test_data:
        return _run_create_test_data(path, COMPOSE_SERVICE_NAME)


def seed_initial_data(
    datastores: List[str],
    path: str,
    service_name: str,
) -> None:
    """
    Seed the datastores with initial data as defined in the file at `setup_path`
    """
    _run_cmd_or_err('echo "Seeding initial data for all datastores..."')
    for datastore in datastores:
        if datastore in DOCKERFILE_DATASTORES:
            setup_path = (
                f"{OPS_TEST_DIR}integration_tests/setup_scripts/{datastore}_setup.py"
            )
            _run_cmd_or_err(
                f'echo "Attempting to create schema and seed initial data for {datastore} from {setup_path}..."'
            )
            _run_cmd_or_err(
                f'docker-compose {path} run {service_name} python {setup_path} || echo "no custom setup logic found for {datastore}, skipping"'
            )


def get_path_for_datastores(datastores: List[str]) -> str:
    """
    Returns the docker-compose file paths for the specified datastores
    """
    path: str = "-f docker-compose.yml"
    for datastore in datastores:
        _run_cmd_or_err(f'echo "configuring infrastructure for {datastore}"')
        if datastore in DOCKERFILE_DATASTORES:
            # We only need to locate the docker-compose file if the datastore runs in Docker
            path += f" -f docker/docker-compose.integration-{datastore}.yml"
        elif datastore not in EXTERNAL_DATASTORES:
            # If the specified datastore is not known to us
            _run_cmd_or_err(f'echo "Datastore {datastore} is currently not supported"')

    return path


def _run_cmd_or_err(cmd: str) -> None:
    """
    Runs a command in the bash prompt and throws an error if the command was not successful
    """
    with subprocess.Popen(cmd, shell=True) as result:
        if result.wait() > 0:
            raise Exception(f"Error executing command: {cmd}")


def _run_quickstart(
    path: str,
    service_name: str,
) -> None:
    """
    Invokes the Fidesops command line quickstart
    """
    _run_cmd_or_err('echo "Running the quickstart..."')
    _run_cmd_or_err(f"docker-compose {path} up -d")
    _run_cmd_or_err(f"docker-compose run {service_name} python scripts/quickstart.py")


def _run_create_test_data(
    path: str,
    service_name: str,
) -> None:
    """
    Invokes the Fidesops create_user_and_client command
    """
    _run_cmd_or_err('echo "Running create test data..."')
    _run_cmd_or_err(f"docker-compose {path} up -d")
    _run_cmd_or_err(
        f"docker-compose run {service_name} python scripts/create_test_data.py"
    )


def _open_shell(
    path: str,
    service_name: str,
) -> None:
    """
    Opens a bash shell on the container at `service_name`
    """
    _run_cmd_or_err(f'echo "Opening bash shell on {service_name}"')
    _run_cmd_or_err(f"docker-compose {path} run {service_name} /bin/bash")


def _run_application(docker_compose_path: str) -> None:
    """
    Runs the application at `docker_compose_path` without detaching it from the shell
    """
    _run_cmd_or_err('echo "Running application"')
    _run_cmd_or_err(f"docker-compose {docker_compose_path} up")


def _run_tests(
    datastores: List[str],
    docker_compose_path: str,
    pytest_path: str = "",
    analytics_opt_out: bool = False,
) -> None:
    """
    Runs unit tests against the specified datastores
    """
    if pytest_path is None:
        pytest_path = ""

    path_includes_markers = "-m" in pytest_path
    pytest_markers: str = ""
    if not path_includes_markers:
        # If the path manually specified already uses markers, don't add more here
        if set(datastores) == set(DOCKERFILE_DATASTORES + EXTERNAL_DATASTORES):
            # If all datastores have been specified use the generic `integration` flag
            pytest_markers += "integration"
        else:
            # Otherwise only include the datastores provided
            for datastore in datastores:
                if len(pytest_markers) == 0:
                    pytest_markers += f"integration_{datastore}"
                else:
                    pytest_markers += f" or integration_{datastore}"

    environment_variables = ""
    for datastore in EXTERNAL_DATASTORES:
        if datastore in datastores:
            for env_var in EXTERNAL_DATASTORE_CONFIG[datastore]:
                environment_variables += f"-e {env_var} "

    if analytics_opt_out:
        environment_variables += "-e ANALYTICS_OPT_OUT"

    pytest_path += f' -m "{pytest_markers}"'

    _run_cmd_or_err(
        f'echo "running pytest for conditions: {pytest_path} with environment variables: {environment_variables}"'
    )
    _run_cmd_or_err(
        f"docker-compose {docker_compose_path} run {environment_variables} {COMPOSE_SERVICE_NAME} pytest {pytest_path}"
    )

    # Now tear down the infrastructure
    _run_cmd_or_err(f"docker-compose {docker_compose_path} down --remove-orphans")
    _run_cmd_or_err('echo "fin."')


if __name__ == "__main__":
    if sys.version_info.major < 3:
        raise Exception("Python3 is required to configure Fidesops.")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--datastores",
        action="extend",
        nargs="*",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--run_tests",
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--pytest_path",
    )
    parser.add_argument(
        "-s",
        "--open_shell",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--run_application",
        action="store_true",
    )
    parser.add_argument(
        "-q",
        "--run_quickstart",
        action="store_true",
    )

    parser.add_argument(
        "-a",
        "--analytics_opt_out",
        action="store_true",
    )

    config_args = parser.parse_args()

    run_infrastructure(
        datastores=config_args.datastores,
        open_shell=config_args.open_shell,
        pytest_path=config_args.pytest_path,
        run_application=config_args.run_application,
        run_quickstart=config_args.run_quickstart,
        run_tests=config_args.run_tests,
        analytics_opt_out=config_args.analytics_opt_out,
    )
