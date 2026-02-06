"""The root module for the Fides package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ethyca-fides")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
