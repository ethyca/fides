"""Unit tests for the engine module's Python-side logic.

Tests the library search, platform detection, and error handling
WITHOUT requiring the Go shared library to be built. The Go
evaluation logic is tested in Go (policy-engine/pkg/).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from fides.service.pbac.engine import _lib_filename, find_library


class TestLibFilename:
    def test_darwin(self):
        with patch("fides.service.pbac.engine.platform.system", return_value="Darwin"):
            assert _lib_filename() == "libpbac.dylib"

    def test_linux(self):
        with patch("fides.service.pbac.engine.platform.system", return_value="Linux"):
            assert _lib_filename() == "libpbac.so"

    def test_windows(self):
        with patch("fides.service.pbac.engine.platform.system", return_value="Windows"):
            assert _lib_filename() == "libpbac.dll"


class TestFindLibrary:
    def test_finds_installed_binary(self):
        """find_library locates a real libpbac binary."""
        result = find_library()
        assert result.is_file()
        assert result.name.startswith("libpbac")

    def test_raises_with_searched_paths_when_not_found(self, monkeypatch):
        """RuntimeError lists searched paths when library isn't anywhere."""
        monkeypatch.setattr(Path, "is_file", lambda self: False)
        monkeypatch.setattr("importlib.util.find_spec", lambda name: None)

        with pytest.raises(RuntimeError, match="Searched"):
            find_library()
