"""Fides CLI"""

from fides.ctl.core.config import get_config
from fides.ctl.core.config.utils import check_if_required_config_vars_are_configured

check_if_required_config_vars_are_configured()

from ._version import get_versions

# Load the config here as a work around to the timing issue with environment variables
get_config()

__version__ = get_versions()["version"]
del get_versions
