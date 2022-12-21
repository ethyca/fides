import webbrowser
from functools import partial
from os import environ, getcwd, makedirs
from os.path import dirname, exists, join
from subprocess import DEVNULL, PIPE, STDOUT, CalledProcessError, run
from typing import List

from click import echo

import fides
from fides.cli.utils import FIDES_ASCII_ART
from fides.core.utils import echo_green, echo_red

FIDES_UPLOADS_DIR = getcwd() + "/fides_uploads/"
REQUIRED_DOCKER_VERSION = "20.10.17"
SAMPLE_PROJECT_DIR = join(
    dirname(__file__),
    "../data/sample_project",
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
        run("docker info", stdout=DEVNULL, stderr=STDOUT, check=True, shell=True)
        raw = run("docker --version", stdout=PIPE, check=True, shell=True)
    except CalledProcessError:
        raise SystemExit(
            "Error: Could not determine Docker version from 'docker' commands. Please ensure that Docker is running and try again."
        )

    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    # We need to handle multiple possible version formats here
    # Docker version 20.10.17, build 100c701
    # Docker version 20.10.18+azure-1, build b40c2f6
    docker_version = parsed.split("version ")[-1].split(",")[0].split("+")[0]

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
        DOCKER_COMPOSE_COMMAND
        + "run --no-deps --rm fides fides push src/fides/data/sample_project/sample_resources/"
    )
    run_shell(
        DOCKER_COMPOSE_COMMAND
        + "run --no-deps --rm fides python scripts/load_examples.py"
    )


def check_fides_uploads_dir() -> None:
    """
    Create the './fides_uploads/ dir if it doesn't already exist

    This fixes an error that was happening in CI checks related to
    binding a file that doesn't exist.
    """
    if not exists(FIDES_UPLOADS_DIR):
        makedirs(FIDES_UPLOADS_DIR)


def teardown_application() -> None:
    """Teardown all of the application containers for fides."""

    # This needs to get set, or else it throws an error
    environ["FIDES_UPLOADS_DIR"] = FIDES_UPLOADS_DIR
    run_shell(DOCKER_COMPOSE_COMMAND + "down --remove-orphans --volumes")


def start_application() -> None:
    """Spin up the application via a docker compose file."""
    environ["FIDES_UPLOADS_DIR"] = FIDES_UPLOADS_DIR
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
    echo(
        f"Pulling ethyca/fides image from DockerHub to match local fides version: {current_fides_version}"
    )

    # Untagged image names
    fides_image_stub = "ethyca/fides:{}"
    privacy_center_image_stub = "ethyca/fides-privacy-center:{}"
    sample_app_image_stub = "ethyca/fides-sample-app:{}"

    # Tagged with the current application version
    current_fides_image = fides_image_stub.format(current_fides_version)
    current_privacy_center_image = privacy_center_image_stub.format(
        current_fides_version
    )
    current_sample_app_image = sample_app_image_stub.format(current_fides_version)

    # Tagged with `dev`
    dev_fides_image = fides_image_stub.format("dev")
    dev_privacy_center_image = privacy_center_image_stub.format("dev")
    dev_sample_app_image = sample_app_image_stub.format("dev")

    try:
        echo("Attempting to pull:")
        echo(f"- {current_fides_image}")
        echo(f"- {current_privacy_center_image}")
        echo(f"- {current_sample_app_image}")

        run_shell(f"docker pull {current_fides_image}")
        run_shell(f"docker pull {current_privacy_center_image}")
        run_shell(f"docker pull {current_sample_app_image}")
        run_shell(
            f"docker tag {current_fides_image} {fides_image_stub.format('sample')}"
        )
        run_shell(
            f"docker tag {current_privacy_center_image} {privacy_center_image_stub.format('sample')}"
        )
        run_shell(
            f"docker tag {current_sample_app_image} {sample_app_image_stub.format('sample')}"
        )
    except CalledProcessError:
        print("Unable to fetch matching version, defaulting to 'dev' versions...")

        try:
            echo("Attempting to pull:")
            echo(f"- {dev_fides_image}")
            echo(f"- {dev_privacy_center_image}")
            echo(f"- {dev_sample_app_image}")

            run_shell(f"docker pull {dev_fides_image}")
            run_shell(f"docker pull {dev_privacy_center_image}")
            run_shell(f"docker pull {dev_sample_app_image}")
            run_shell(
                f"docker tag {dev_fides_image} {fides_image_stub.format('sample')}"
            )
            run_shell(
                f"docker tag {dev_privacy_center_image} {privacy_center_image_stub.format('sample')}"
            )
            run_shell(
                f"docker tag {dev_sample_app_image} {sample_app_image_stub.format('sample')}"
            )
        except CalledProcessError:
            echo_red("Failed to pull 'dev' versions of docker containers! Aborting...")
            raise SystemExit(1)


def print_deploy_success() -> None:
    """
    Pretty prints an in-depth success message for successful deployment.
    """

    echo_green(FIDES_ASCII_ART)
    echo_green(
        "Sample Fides project successfully deployed and running in the background!"
    )
    echo_green("Next steps:")

    # Landing Page
    echo_green("\n- View the documentation http://localhost:3000/landing")

    # Admin UI
    echo_green("\n- Visit the Fides Admin UI running at http://localhost:8080")
    echo_green("    (user=fidestest, password=Apassword1!)")

    # Sample App
    echo_green("\n- Sample 'Cookie House' Application running at http://localhost:3000")
    echo_green("\n- Sample Privacy Center running at http://localhost:3001")
    echo_green("    (user=jane@example.com)")

    # Example Databases
    echo_green("\n- Example Postgres Database running at localhost:6432")
    echo_green("    (user=postgres, password=postgres, db=postgres_example)")
    echo_green("\n- Example Mongo Database running at localhost:37017")
    echo_green("    (user=mongo_test, password=mongo_pass, db=mongo_test)")

    # Documentation
    echo_green("\n- Visit ethyca.github.io/fides for documentation.")
    echo_green("\nRun `fides deploy down` to stop the application.")

    # Open the landing page and DSR directory
    webbrowser.open("http://localhost:3000/landing")
    webbrowser.open(f"file:///{FIDES_UPLOADS_DIR}")
