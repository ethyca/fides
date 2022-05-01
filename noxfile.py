"""This file aggregates nox commands for various development tasks."""
import sys

import nox

sys.path.append("noxfiles")
from ci_nox import *
from dev_nox import *
from docker_nox import *
from docs_nox import *
from utils_nox import *

# Sets the default session to `--list`
nox.options.sessions = []
