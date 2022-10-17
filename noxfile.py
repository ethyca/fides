"""
This file aggregates nox commands for various development tasks.
"""
import sys
import shutil
from os.path import isfile

import nox

sys.path.append("noxfiles")
from ci_nox import *
from dev_nox import *
from docker_nox import *
from docs_nox import *
from utils_nox import *

# Sets the default session to `--list`
nox.options.sessions = []
nox.options.reuse_existing_virtualenvs = True


def check_for_env_file() -> None:
    """Create a .env file if none exists."""
    env_file_example = "example.env"
    env_file = ".env"
    if not isfile(env_file):
        print(f"Creating env file for local testing & development from {env_file_example}: {env_file}")
        shutil.copy(env_file_example, env_file)


check_for_env_file()
