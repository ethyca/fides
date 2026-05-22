"""Unit tests for the engine module's Python-side logic.

Tests the library search, platform detection, and error handling
WITHOUT requiring the Go shared library to be built. The Go
evaluation logic is tested in Go (policy-engine/pkg/).
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from fides.service.pbac.engine import _find_library, _lib_filename


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
    def test_env_var_override(self, tmp_path):
        """FIDES_PBAC_LIB_PATH pointing to a real file wins."""
        lib_file = tmp_path / "libpbac.so"
        lib_file.write_text("fake")
        with patch.dict(os.environ, {"FIDES_PBAC_LIB_PATH": str(lib_file)}):
            assert _find_library() == lib_file

    def test_env_var_nonexistent_file_falls_through(self, tmp_path):
        """FIDES_PBAC_LIB_PATH pointing to missing file is ignored."""
        with patch.dict(os.environ, {"FIDES_PBAC_LIB_PATH": str(tmp_path / "nope")}):
            # Mock out the fallback paths so we get RuntimeError
            with patch.object(Path, "is_file", return_value=False):
                with pytest.raises(RuntimeError, match="Could not find"):
                    _find_library()

    def test_raises_when_no_library_found(self):
        """RuntimeError when library isn't at any search location."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FIDES_PBAC_LIB_PATH", None)
            with patch.object(Path, "is_file", return_value=False):
                with pytest.raises(RuntimeError, match="Could not find"):
                    _find_library()

    def test_error_message_includes_build_command(self):
        """Error message tells users how to build the library."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FIDES_PBAC_LIB_PATH", None)
            with patch.object(Path, "is_file", return_value=False):
                with pytest.raises(RuntimeError, match="go build -buildmode=c-shared"):
                    _find_library()
