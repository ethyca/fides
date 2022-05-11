"""
This file invokes a command used to setup infrastructure for use in testing Fidesops
and related workflows.
"""
import argparse
import subprocess
import sys
from typing import (
    List,
)


DOCKER_WAIT = 5
DOCKERFILE_DATASTORES = [
    "mssql",
    "postgres",
    "mysql",
    "mongodb",
    "mariadb",
]
EXTERNAL_DATASTORE_CONFIG = {
    "snowflake": ["SNOWFLAKE_TEST_URI"],
    "redshift": ["REDSHIFT_TEST_URI", "REDSHIFT_TEST_DB_SCHEMA"],
    "bigquery": ["BIGQUERY_KEYFILE_CREDS", "BIGQUERY_DATASET"],
}
EXTERNAL_DATASTORES = list(EXTERNAL_DATASTORE_CONFIG.keys())
IMAGE_NAME = "fidesops"


def run_infrastructure(
    datastores: List[str] = [],  # Which infra should we create? If empty, we create all
    open_shell: bool = False,  # Should we open a bash shell?
    pytest_path: str = "",  # Which subset of tests should we run?
    run_application: bool = False,  # Should we run the Fidesops webserver?
    run_quickstart: bool = False,  # Should we run the quickstart command?
    run_tests: bool = False,  # Should we run the tests after creating the infra?
    run_create_superuser: bool = False,  # Should we run the create_superuser command?
    run_create_test_data: bool = False,  # Should we run the create_test_data command?
) -> None:
    """
    - Create a Docker Compose file path for all datastores specified in `datastores`.
    - Defaults to creating infrastructure for all datastores in `DOCKERFILE_DATASTORES` if none
    are provided.
    - Optionally runs integration tests against those datastores from the container identified
    with `IMAGE_NAME`.
    """

    if len(datastores) == 0:
        _run_cmd_or_err(
            f'echo "no datastores specified, configuring infrastructure for all datastores"'
        )
        datastores = DOCKERFILE_DATASTORES + EXTERNAL_DATASTORES
    else:
        _run_cmd_or_err(f'echo "datastores specified: {", ".join(datastores)}"')

    # De-duplicate datastores
    datastores = set(datastores)

    # Configure docker-compose path
    path: str = get_path_for_datastores(datastores)

    _run_cmd_or_err(f'echo "infrastructure path: {path}"')
    if "mssql" in datastores:
        _run_cmd_or_err(
            f'docker-compose {path} build --build-arg MSSQL_REQUIRED="true"'
        )
    _run_cmd_or_err(f"docker-compose {path} up -d")
    _run_cmd_or_err(f'echo "sleeping for: {DOCKER_WAIT} while infrastructure loads"')

    wait = min(DOCKER_WAIT * len(datastores), 15)
    _run_cmd_or_err(f"sleep {wait}")

    seed_initial_data(
        datastores,
        path,
        base_image=IMAGE_NAME,
    )

    if open_shell:
        return _open_shell(path, IMAGE_NAME)

    elif run_application:
        return _run_application(path)

    elif run_quickstart:
        return _run_quickstart(path, IMAGE_NAME)

    elif run_tests:
        # Now run the tests
        return _run_tests(
            datastores,
            docker_compose_path=path,
            pytest_path=pytest_path,
        )

    elif run_create_superuser:
        return _run_create_superuser(path, IMAGE_NAME)

    elif run_create_test_data:
        return _run_create_test_data(path, IMAGE_NAME)


def seed_initial_data(
    datastores: List[str],
    path: str,
    base_image: str,
) -> None:
    """
    Seed the datastores with initial data as defined in the file at `setup_path`
    """
    _run_cmd_or_err('echo "Seeding initial data for all datastores..."')
    for datastore in datastores:
        if datastore in DOCKERFILE_DATASTORES:
            setup_path = f"tests/integration_tests/setup_scripts/{datastore}_setup.py"
            _run_cmd_or_err(
                f'echo "Attempting to create schema and seed initial data for {datastore} from {setup_path}..."'
            )
            _run_cmd_or_err(
                f'docker-compose {path} run {base_image} python {setup_path} || echo "no custom setup logic found for {datastore}, skipping"'
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
            path += f" -f docker-compose.integration-{datastore}.yml"
        elif datastore not in EXTERNAL_DATASTORES:
            # If the specified datastore is not known to us
            _run_cmd_or_err(f'echo "Datastore {datastore} is currently not supported"')

    return path


def _run_cmd_or_err(cmd: str) -> None:
    """
    Runs a command in the bash prompt and throws an error if the command was not successful
    """
    res = subprocess.Popen(cmd, shell=True).wait()
    if res > 0:
        raise Exception(f"Error executing command: {cmd}")


def _run_quickstart(
    path: str,
    image_name: str,
) -> None:
    """
    Invokes the Fidesops command line quickstart
    """
    _run_cmd_or_err(f'echo "Running the quickstart..."')
    _run_cmd_or_err(f"docker-compose {path} up -d")
    _run_cmd_or_err(f"docker exec -it {image_name} python quickstart.py")


def _run_create_superuser(
    path: str,
    image_name: str,
) -> None:
    """
    Invokes the Fidesops create_user_and_client command
    """
    _run_cmd_or_err(f'echo "Running create superuser..."')
    _run_cmd_or_err(f"docker-compose {path} up -d")
    _run_cmd_or_err(f"docker exec -it {image_name} python create_superuser.py")


def _run_create_test_data(
    path: str,
    image_name: str,
) -> None:
    """
    Invokes the Fidesops create_user_and_client command
    """
    _run_cmd_or_err(f'echo "Running create superuser..."')
    _run_cmd_or_err(f"docker-compose {path} up -d")
    _run_cmd_or_err(f"docker exec -it {image_name} python create_test_data.py")


def _open_shell(
    path: str,
    image_name: str,
) -> None:
    """
    Opens a bash shell on the container at `image_name`
    """
    _run_cmd_or_err(f'echo "Opening bash shell on {image_name}"')
    _run_cmd_or_err(f"docker-compose {path} run {image_name} /bin/bash")


def _run_application(docker_compose_path: str) -> None:
    """
    Runs the application at `docker_compose_path` without detaching it from the shell
    """
    _run_cmd_or_err(f'echo "Running application"')
    _run_cmd_or_err(f"docker-compose {docker_compose_path} up")


def _run_tests(
    datastores: List[str],
    docker_compose_path: str,
    pytest_path: str = "",
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

    pytest_path += f' -m "{pytest_markers}"'

    _run_cmd_or_err(
        f'echo "running pytest for conditions: {pytest_path} with environment variables: {environment_variables}"'
    )
    _run_cmd_or_err(
        f"docker-compose {docker_compose_path} run {environment_variables} {IMAGE_NAME} pytest {pytest_path}"
    )

    # Now tear down the infrastructure
    _run_cmd_or_err(f"docker-compose {docker_compose_path} down --remove-orphans")
    _run_cmd_or_err(f'echo "fin."')


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
        "-su",
        "--run_create_superuser",
        action="store_true",
    )

    parser.add_argument(
        "-td",
        "--run_create_test_data",
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
        run_create_superuser=config_args.run_create_superuser,
        run_create_test_data=config_args.run_create_test_data,
    )
