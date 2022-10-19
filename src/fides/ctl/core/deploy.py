import shutil
from os.path import isfile
from subprocess import PIPE, CalledProcessError, run
from typing import List
import shutil
from os.path import dirname, join
from typing import List

REQUIRED_DOCKER_VERSION = "20.10.17"

DOCKER_COMPOSE_FILE = join(
    dirname(__file__),
    "../../data",
    "fides-application.docker-compose.yml",
)


def check_for_env_file() -> None:
    """Create a .env file if none exists."""
    env_file_example = "example.env"
    env_file = ".env"
    if not isfile(env_file):
        print(
            f"Creating env file for local testing & development from {env_file_example}: {env_file}"
        )
        shutil.copy(env_file_example, env_file)


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


def start_application() -> None:
    """Spin up the application via a docker compose file."""
    run(
        f"docker compose -f {DOCKER_COMPOSE_FILE} up",
        shell=True,
        check=True,
    )
