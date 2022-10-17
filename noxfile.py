"""
This file aggregates nox commands for various development tasks.

To learn more about nox, visit https://nox.thea.codes/en/stable/index.html
"""
import sys
from subprocess import PIPE, run

import nox

sys.path.append("noxfiles")
from ci_nox import *
from dev_nox import *
from docker_nox import *
from docs_nox import *
from utils_nox import *

REQUIRED_DOCKER_VERSION = "20.10.17"

# Sets the default session to `--list`
nox.options.sessions = []
nox.options.reuse_existing_virtualenvs = True


def check_docker_version() -> bool:
    """Verify the Docker version."""
    raw = run("docker --version", stdout=PIPE, check=True, shell=True)
    parsed = raw.stdout.decode("utf-8").rstrip("\n")
    print(parsed)

    docker_version = parsed.split("version ")[-1].split(",")[0]
    version_is_valid = int(docker_version.replace(".", "")) >= int(
        REQUIRED_DOCKER_VERSION.replace(".", "")
    )
    if not version_is_valid:
        raise SystemExit(
            f"Your Docker version (v{docker_version}) is not compatible, please update to at least version {REQUIRED_DOCKER_VERSION}!"
        )
    return version_is_valid


check_docker_version()
