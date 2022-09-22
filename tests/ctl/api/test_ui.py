# pylint: disable=missing-docstring, redefined-outer-name
import re
from pathlib import Path
from typing import Dict

import pytest

from fides.api.ctl.ui import generate_route_file_map, match_route

# Path segments of temporary files whose routes are tested.
STATIC_FILES = (
    "index.html",
    "404.html",
    "dataset.html",
    "dataset/new.html",
    "dataset/[id].html",
    "nested/[...slug].html",
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
        ("dataset/G00d-Times_R011/", "dataset/[id].html"),
        ("nested/you/me/and", "nested/[...slug].html"),
        ("nested/the_devil/makes/3/", "nested/[...slug].html"),
    ],
)
def test_match_route(
    tmp_static: Path, route_file_map: Dict[re.Pattern, Path], route: str, expected: str
) -> None:

    # Test example routes.
    assert match_route(route_file_map, route) == tmp_static / expected
