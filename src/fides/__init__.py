"""The root module for the Fides package."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_package_version

from .common.utils import clean_version

try:
    __version__ = clean_version(get_package_version("ethyca-fides"))
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
