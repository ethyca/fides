"""
This file aggregates nox commands for various development tasks.
"""
import sys
from os.path import isfile
from pathlib import Path

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
    """Create a .env file is none exists."""
    env_file = ".env.example"
    if not isfile(env_file):
        print(f"Creating env file: {env_file}")
        Path(env_file).touch()


check_for_env_file()
