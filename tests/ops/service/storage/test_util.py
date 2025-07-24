import os
from typing import Optional

import pytest
from pytest import param

from fides.api.service.storage.util import (
    AllowedFileType,
    get_allowed_file_type_or_raise,
    get_local_filename,
)


@pytest.mark.parametrize(
    "file_key, expected_file_type",
    [
        param("test.pdf", AllowedFileType.pdf.value, id="pdf"),
        param("test.docx", AllowedFileType.docx.value, id="docx"),
        param("test.txt", AllowedFileType.txt.value, id="txt"),
        param(
            "test.not_a_file_type.txt",
            AllowedFileType.txt.value,
            id="not_a_file_type_dot_txt",
        ),
        param("test.jpg", AllowedFileType.jpg.value, id="jpg"),
        param("test.jpeg", AllowedFileType.jpeg.value, id="jpeg"),
        param("test.png", AllowedFileType.png.value, id="png"),
        param("test.xls", AllowedFileType.xls.value, id="xls"),
        param("test.xlsx", AllowedFileType.xlsx.value, id="xlsx"),
        param("test.csv", AllowedFileType.csv.value, id="csv"),
        param("test.zip", AllowedFileType.zip.value, id="zip"),
        param(
            "test.not_a_file_type.txt.pdf",
            AllowedFileType.pdf.value,
            id="not_a_file_type_dot_txt_dot_pdf",
        ),
        param("test.yaml", None, id="yaml"),
        param("test", None, id="no_extension"),
        param("test.", None, id="no_extension_dot"),
        param("test.not_a_file_type", None, id="not_a_file_type"),
    ],
)
def test_get_file_type(file_key: str, expected_file_type: Optional[str]):
    """Test that the get_file_type function returns the correct file type"""
    if expected_file_type is None:
        with pytest.raises(ValueError) as excinfo:
            get_allowed_file_type_or_raise(file_key)
            assert "Invalid or unallowed file extension" in str(excinfo.value)
    else:
        assert get_allowed_file_type_or_raise(file_key) == expected_file_type


class TestGetLocalFilename:
    """Tests for the get_local_filename function"""

    def test_valid_filename(self, tmp_path):
        """Test that a valid filename returns the correct path"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "fides.api.service.storage.util.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
            result = get_local_filename("test.txt")
            assert result == str(tmp_path / "test.txt")
            assert os.path.exists(tmp_path)

    def test_empty_filename(self):
        """Test that an empty filename raises ValueError"""
        with pytest.raises(ValueError) as excinfo:
            get_local_filename("")
        assert "File key cannot be empty" in str(excinfo.value)

    def test_absolute_path_attempt(self, tmp_path):
        """Test that absolute paths are blocked"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "fides.api.service.storage.util.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
            with pytest.raises(ValueError) as excinfo:
                get_local_filename("/test.txt")
            assert "start with '/'" in str(excinfo.value)

    @pytest.mark.parametrize(
        "path,description,should_fail",
        [
            param(
                "../test.txt",
                "simple parent directory traversal",
                True,
                id="simple_parent_directory_traversal",
            ),
            param(
                "../../../etc/passwd",
                "multiple parent directory traversal",
                True,
                id="multiple_parent_directory_traversal",
            ),
            param("subdir/../..", "traversal to root", True, id="traversal_to_root"),
            param(
                "subdir/../../",
                "traversal to root with trailing slash",
                True,
                id="traversal_to_root_with_trailing_slash",
            ),
            param(
                "valid/path/../subdir/file.txt",
                "traversal in valid path",
                False,
                id="traversal_in_valid_path",
            ),
            param(
                "valid/path/../../subdir/file.txt",
                "multiple traversal in valid path",
                False,
                id="multiple_traversal_in_valid_path",
            ),
            param(
                "subdir/other/../file.txt",
                "traversal within upload dir",
                False,
                id="traversal_within_upload_dir",
            ),
            param(
                "subdir/other/../../file.txt",
                "multiple traversal within upload dir",
                False,
                id="multiple_traversal_within_upload_dir",
            ),
        ],
    )
    def test_path_traversal_attempts(self, tmp_path, path, description, should_fail):
        """Test various path traversal attempts are blocked or allowed appropriately"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "fides.api.service.storage.util.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
            if should_fail:
                with pytest.raises(ValueError) as excinfo:
                    get_local_filename(path)
                assert "path outside upload directory" in str(
                    excinfo.value
                ), f"Failed to catch {description}"
            else:
                # Should succeed and create the appropriate directory structure
                result = get_local_filename(path)
                assert os.path.exists(os.path.dirname(result))
                # Verify the path is within the upload directory
                assert os.path.abspath(result).startswith(os.path.abspath(tmp_path))

    def test_normalizes_path_separators(self, tmp_path):
        """Test that path separators are normalized correctly"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "fides.api.service.storage.util.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
            result = get_local_filename("test\\subdir\\file.txt")
            assert result == str(tmp_path / "test" / "subdir" / "file.txt")

    def test_creates_nested_directories(self, tmp_path):
        """Test that nested directories are created as needed"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "fides.api.service.storage.util.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
            result = get_local_filename("subdir/nested/file.txt")
            assert result == str(tmp_path / "subdir" / "nested" / "file.txt")
            assert os.path.exists(os.path.dirname(result))

    def test_handles_unicode_filenames(self, tmp_path):
        """Test that unicode filenames are handled correctly"""
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "fides.api.service.storage.util.LOCAL_FIDES_UPLOAD_DIRECTORY",
                str(tmp_path),
            )
            result = get_local_filename("test_文件.txt")
            assert result == str(tmp_path / "test_文件.txt")
            assert os.path.exists(tmp_path)
