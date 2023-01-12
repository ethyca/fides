"""The root module for the Fides package."""
from fides.core.config import get_config

from ._version import get_versions

# Load the config here as a work around to the timing issue with environment variables
get_config()

__version__ = get_versions()["version"]
del get_versions
