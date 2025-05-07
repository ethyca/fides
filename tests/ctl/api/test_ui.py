# pylint: disable=missing-docstring, redefined-outer-name
import re
from pathlib import Path
from typing import Dict
from unittest import mock
from unittest.mock import Mock

import pytest
import requests
from starlette.testclient import TestClient

from fides.api.ui import generate_route_file_map, match_route, path_is_in_ui_directory

# Path segments of temporary files whose routes are tested.
STATIC_FILES = (
    "index.html",
    "404.html",
    "dataset.html",
    "dataset/new.html",
    "dataset/[id].html",
    "nested/[...slug].html",
    "multimatch/[first].html",
)


@pytest.fixture(scope="session")
def tmp_static(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("static")


@pytest.fixture(scope="session")
def route_file_map(tmp_static: Path) -> Dict[re.Pattern, Path]:
    # Generate the temporary files to test against.
    for static_segment in STATIC_FILES:
        static_path = tmp_static / static_segment
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static_path.touch()

    return generate_route_file_map(str(tmp_static))


@pytest.mark.unit
def test_generate_route_file_map(route_file_map: Dict[re.Pattern, Path]) -> None:
    # Ensure all paths in the map are real files.
    for path in route_file_map.values():
        assert path.exists()


@pytest.mark.unit
@pytest.mark.parametrize(
    "route,expected",
    [
        ("index", "index.html"),
        ("dataset", "dataset.html"),
        ("dataset/", "dataset.html"),
        ("dataset/new", "dataset/new.html"),
        ("dataset/1234", "dataset/[id].html"),
        ("dataset/id.with.dots", "dataset/[id].html"),  # should pass right now?
        ("dataset/[id_with_brackets]", "dataset/[id].html"),  # should fail right now?
        ("dataset/G00d-Times_R011/", "dataset/[id].html"),
        ("nested/you/me/and", "nested/[...slug].html"),
        ("nested/the_devil/makes/3/", "nested/[...slug].html"),
        ("multimatch/one", "multimatch/[first].html"),
    ],
)
def test_match_route(
    tmp_static: Path, route_file_map: Dict[re.Pattern, Path], route: str, expected: str
) -> None:
    # Test example routes.
    assert match_route(route_file_map, route) == tmp_static / expected


@pytest.mark.unit
@mock.patch("fides.api.ui.get_path_to_admin_ui_file")
@pytest.mark.parametrize(
    "route, expected",
    [
        ("index.html", True),
        ("//etc/passwd", False),
        ("dataset/new.html", True),
        ("//fides/example.env", False),
    ],
)
def test_path_is_in_ui_directory(
    mock_get_path_to_admin_ui_file: Mock, tmp_static: Path, route: str, expected: bool
):
    """Test various paths for if they are in the UI directory"""
    mock_get_path_to_admin_ui_file.return_value = tmp_static
    assert path_is_in_ui_directory(tmp_static / Path(route)) == expected


@pytest.mark.integration
@pytest.mark.parametrize("route, expected", [("/", 200), ("//etc/passwd", 404)])
def test_check_file_within_ui_directory(
    test_client: TestClient, route: str, expected: int
):
    """Test attempts at retrieving files outside the UI directory"""
    # We use localhost:8080 here because otherwise TestClient will strip out
    # the leading `//` for malicious paths
    res = test_client.get(f"http://localhost:8080{route}")
    assert res.status_code == expected
