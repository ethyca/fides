"""Various functions to help serve the UI from our server"""

import importlib.util
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Union

from fastapi import Response
from fastapi.responses import FileResponse
from loguru import logger

FIDES_DIRECTORY = "src/fides"
ADMIN_UI_DIRECTORY = "ui-build/static/admin/"


def get_package_path() -> Optional[Path]:
    """
    Returns a Path to the root directory of this package's installation, if it exists.

    If installed via `pip install -e` (like in Dockerfile's `dev` target), this may be /fides/src/fides
    If installed via `pip install ethyca-fides`, this will be more like /usr/local/lib/python/site-packages/fides
    """
    package_name = __package__.split(".", maxsplit=1)[0]
    spec = importlib.util.find_spec(package_name)
    if spec and spec.origin:
        return Path(spec.origin).parent

    return None


def get_path_to_admin_ui_file(path: str = "") -> Optional[Path]:
    """
    Return a path to a packaged admin UI file.

    If no path is given, returns the path to the root of the UI directory
    """
    package_path = get_package_path()
    if package_path is None:
        return None

    return package_path / ADMIN_UI_DIRECTORY / path


def get_admin_index_as_response() -> Response:
    """Get just the frontend index file as a FileResponse.
    If it does not exist, return a placeholder."""
    placeholder = "<h1>Privacy is a Human Right!</h1>"
    index = get_path_to_admin_ui_file("index.html")
    return FileResponse(index) if index and index.is_file() else Response(placeholder)


@lru_cache
def get_ui_file_map() -> Dict[re.Pattern, Path]:
    """Get the Admin UI route map from its static files."""
    package_path = get_package_path()
    if package_path is None:
        return {}

    return generate_route_file_map(package_path / ADMIN_UI_DIRECTORY)


def generate_route_file_map(ui_directory: Union[str, Path]) -> Dict[re.Pattern, Path]:
    """
    Generates a map of route patterns to the paths of files that route should serve.
    The returned paths are absolute (not relative to ui_directory or CWD).

    :param ui_directory: The path (or str) of the directory to search for route-able files.
    """
    ui_path = Path(ui_directory)
    if not ui_path.exists():
        return {}

    exact_pattern = r"\[[a-zA-Z]+\]"
    nested_pattern = r"\[...[a-zA-Z]+\]"

    exact_pattern_replacement = r"[a-zA-Z10-9-_]+"
    nested_pattern_replacement = r"[a-zA-Z10-9-_/]+"

    route_file_map = {}

    for filepath in ui_path.glob("**/*.html"):
        # Ignore directory root.
        if filepath == ui_path:
            continue

        # Path within the ui_directory, with the file extension (.html) removed.
        relative_path = filepath.relative_to(ui_path).with_suffix("")

        route = str(relative_path)
        if re.search(exact_pattern, str(relative_path)):
            route = re.sub(exact_pattern, exact_pattern_replacement, str(relative_path))
        if re.search(nested_pattern, str(filepath)):
            route = re.sub(
                nested_pattern,
                nested_pattern_replacement,
                str(relative_path),
            )

        # Full match, allowing trailing slash.
        pattern = re.compile(r"^" + route + r"/?$")

        route_file_map[pattern] = filepath

    return route_file_map


def match_route(route_file_map: Dict[re.Pattern, Path], route: str) -> Optional[Path]:
    """
    Match a route against a route file map and return the match, if any.

    If multiple routes match, prefers static routes (e.g. dataset/new) over
    dynamic (e.g. dataset/[id]).
    """
    matches = [
        path for pattern, path in route_file_map.items() if re.fullmatch(pattern, route)
    ]

    if not matches:
        return None

    if len(matches) == 1:
        return matches[0]

    # Multiple matches were found, so look for the first static path
    static_matches = [path for path in matches if not _is_dynamic_path(path)]
    if static_matches:
        return sorted(static_matches)[0]

    # If no static matches exist, fallback to the first match
    return sorted(matches)[0]


def path_is_in_ui_directory(path: Path) -> bool:
    """Checks if the path exists within the UI directory"""
    ui_directory = get_path_to_admin_ui_file()
    if not ui_directory:
        logger.debug("Unable to locate UI directory")
        return False

    return ui_directory in path.parents


def _is_dynamic_path(path: Path) -> bool:
    """Returns true if the given route is a dynamic NextJS route (e.g. "dataset/[id].html")"""
    return re.compile(r"\[\w+\]").search(str(path)) is not None
