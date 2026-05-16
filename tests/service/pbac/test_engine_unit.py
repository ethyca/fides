"""Unit tests for the engine module's Python-side logic.

Tests the library search, platform detection, and error handling
WITHOUT requiring the Go shared library to be built. The Go
evaluation logic is tested in Go (policy-engine/pkg/).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

import fides
from fides.service.pbac.engine import _lib_filename, find_library

_pkg_bin = Path(fides.__file__).parent / "bin" / _lib_filename()


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


_has_libpbac = _pkg_bin.is_file()


class TestFindLibrary:
    @pytest.mark.skipif(
        not _has_libpbac, reason="libpbac not built (Go toolchain required)"
    )
    def test_finds_installed_binary(self):
        """Normal install: find_library returns the binary from fides/bin/."""
        result = find_library()
        assert result == _pkg_bin
        assert result.is_file()

    @pytest.mark.skipif(
        not _has_libpbac, reason="libpbac not built (Go toolchain required)"
    )
    def test_importlib_fallback_resolves_same_path(self):
        """importlib.util.find_spec points to the same package the binary lives in."""
        spec = importlib.util.find_spec("fides")
        assert spec is not None
        assert spec.origin is not None
        site_bin = Path(spec.origin).parent / "bin" / _lib_filename()
        assert site_bin.is_file()

    def test_raises_with_searched_paths_when_not_found(self, monkeypatch):
        """RuntimeError lists searched paths when library isn't anywhere."""
        monkeypatch.setattr(Path, "is_file", lambda self: False)
        monkeypatch.setattr("importlib.util.find_spec", lambda name: None)

        with pytest.raises(RuntimeError, match="Searched"):
            find_library()
