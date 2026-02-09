"""The root module for the Fides package."""

import json
from importlib.metadata import PackageNotFoundError, distribution
from importlib.metadata import version as get_package_version

from ._version import get_versions
from .common.utils import clean_version


def _is_editable_install() -> bool:
    """Check if fides is installed as an editable install (pip install -e)."""
    try:
        dist = distribution("ethyca-fides")
        direct_url_text = dist.read_text("direct_url.json")
        if direct_url_text is None:
            return False
        direct_url = json.loads(direct_url_text)
        return direct_url.get("dir_info", {}).get("editable", False)
    except (PackageNotFoundError, FileNotFoundError, json.JSONDecodeError, TypeError):
        return False


def _get_version() -> str:
    """
    Get the package version from one of two sources:

    1. Package metadata (production): When fides is installed as a built package,
       the version is read from package metadata. The Dockerfile runs `python setup.py
       sdist` which uses versioneer to bake the version from git into _version.py.

    2. Versioneer runtime (development): When running from source, editable install,
       or when package metadata isn't available, versioneer reads git directly.

    For editable installs, we prefer versioneer since the package metadata version
    is baked at install time and becomes stale as new commits are made.

    The version is cleaned via clean_version() to strip noisy suffixes for display.
    """
    # For editable installs, prefer versioneer (reads current git state)
    # Package metadata in editable installs is stale from install time
    if _is_editable_install():
        return clean_version(get_versions()["version"])

    # Try to get version from installed package metadata
    # This works for installed packages and doesn't require git at runtime
    try:
        return clean_version(get_package_version("ethyca-fides"))
    except PackageNotFoundError:
        pass

    # Fall back to versioneer for running from source without install
    return clean_version(get_versions()["version"])


__version__ = _get_version()
