"""Various functions to help serve the UI from our server"""

import importlib.util
from pathlib import Path
from typing import Optional

from fastapi import Response
from fastapi.responses import FileResponse

ADMIN_UI_DIRECTORY = "ui-build/static/admin/"


def get_path_to_ui_file(package_name: str, path: str) -> Optional[Path]:
    """Return a path to a UI file within a given package"""
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return None
    return Path(spec.origin).parent / path if spec.origin else None


def get_path_to_admin_ui_file(path: str) -> Optional[Path]:
    """Return a path to an admin UI file."""
    package_name = __package__.split(".")[0]
    return get_path_to_ui_file(package_name, ADMIN_UI_DIRECTORY + path)


def get_admin_index_as_response() -> Response:
    """Get just the frontend index file as a FileResponse.
    If it does not exist, return a placeholder."""
    placeholder = "<h1>Privacy is a Human Right!</h1>"
    index = get_path_to_admin_ui_file("index.html")
    return FileResponse(index) if index and index.is_file() else Response(placeholder)
