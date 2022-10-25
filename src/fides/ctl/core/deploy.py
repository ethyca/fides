from functools import partial
from os.path import dirname, join
from subprocess import PIPE, CalledProcessError, run
from typing import List

import fides
from fides.ctl.core.config import get_config

CONFIG = get_config()
REQUIRED_DOCKER_VERSION = "20.10.17"
SAMPLE_PROJECT_DIR = join(
    dirname(__file__),
    "../../data/sample_project",
)
DOCKER_COMPOSE_FILE = join(SAMPLE_PROJECT_DIR, "docker-compose.yml")
DOCKER_COMPOSE_COMMAND = (
    f"docker compose --project-directory {SAMPLE_PROJECT_DIR} -f {DOCKER_COMPOSE_FILE} "
)
run_shell = partial(run, shell=True, check=True)


def convert_semver_to_list(semver: str) -> List[int]:
    """
    Convert a standard semver string to a list of ints

    '2.10.7' -> [2,10,7]
    """
    return [int(x) for x in semver.split(".")]


def compare_semvers(version_a: List[int], version_b: List[int]) -> bool:
    """
    Determine which semver-style list of integers is larger.

    [2,10,3], [2,10,2] -> True
    [3,1,3], [2,10,2] -> True
    [2,10,2], [2,10,2] -> True
    [1,1,3], [2,10,2] -> False
    """

    major, minor, patch = [0, 1, 2]
    # Compare Major Versions
    if version_a[major] > version_b[major]:
        return True
    if version_a[major] < version_b[major]:
        return False

    # If Major Versions Match, Compare Minor Versions
    if version_a[minor] > version_b[minor]:
        return True
    if version_a[minor] < version_b[minor]:
        return False

    # If Both Major & Minor Versions Match, Compare Patch Versions
    if version_a[patch] < version_b[patch]:
        return False

    return True


def check_docker_version() -> bool:
    """Verify the Docker version."""
    try:
        raw = run("docker --version", stdout=PIPE, check=True, shell=True)
    except CalledProcessError:
        raise SystemExit("Error: Command 'docker' is not available.")

    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    # We need to handle multiple possible version formats here
    # Docker version 20.10.17, build 100c701
    # Docker version 20.10.18+azure-1, build b40c2f6
    docker_version = parsed.split("version ")[-1].split(",")[0].split("+")[0]
    print(parsed)

    split_docker_version = convert_semver_to_list(docker_version)
    split_required_docker_version = convert_semver_to_list(REQUIRED_DOCKER_VERSION)

    if len(split_docker_version) != 3:
        raise SystemExit(
            "Error: Docker version format is invalid, expecting semver format. Please upgrade to a more recent version and try again"
        )

    version_is_valid = compare_semvers(
        split_docker_version, split_required_docker_version
    )
    if not version_is_valid:
        raise SystemExit(
            f"Error: Your Docker version (v{docker_version}) is not compatible, please update to at least version {REQUIRED_DOCKER_VERSION}!"
        )
    return version_is_valid


def seed_example_data() -> None:
    run_shell(
        DOCKER_COMPOSE_COMMAND + "run --no-deps --rm fides fides push demo_resources/"
    )
    run_shell(
        DOCKER_COMPOSE_COMMAND
        + "run --no-deps --rm fides python scripts/load_examples.py"
    )


def teardown_application() -> None:
    """Teardown all of the application containers for fides."""
    run_shell(DOCKER_COMPOSE_COMMAND + "down --remove-orphans --volumes")


def start_application() -> None:
    """Spin up the application via a docker compose file."""
    run_shell(
        DOCKER_COMPOSE_COMMAND + "up --wait",
    )


def pull_specific_docker_image() -> None:
    """
    Pulls a specific docker image version, based on the
    current version of the application.

    If no matching version is found, pull the most recent versions instead.
    """

    current_fides_version = fides.__version__
    print(f"Local fides version: {current_fides_version}")

    try:
        run_shell(f"docker pull ethyca/fides:{current_fides_version}")
        run_shell(f"docker pull ethyca/fides-privacy-center:{current_fides_version}")
    except CalledProcessError:
        run_shell("docker pull ethyca/fides:dev")
        run_shell("docker pull ethyca/fides-privacy-center:latest")
    else:
        run_shell("docker tag ethyca/fides:dev ethyca/fides:sample")
        run_shell("docker tag ethyca/fides-privacy-center:sample")
