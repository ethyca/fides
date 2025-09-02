import os
from typing import Optional

import pytest
from pytest import param

from fides.api.service.storage.util import (
    AllowedFileType,
    get_allowed_file_type_or_raise,
    get_local_filename,
    get_unique_filename,
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


class TestGetUniqueFilename:
    """Tests for the get_unique_filename function"""

    def test_unique_filename_no_conflict(self):
        """Test that a unique filename is returned when no conflicts exist"""
        used_filenames = set()
        result = get_unique_filename("test.txt", used_filenames)
        assert result == "test.txt"
        assert "test.txt" in used_filenames

    def test_unique_filename_with_conflict(self):
        """Test that a unique filename is generated when conflicts exist"""
        used_filenames = {"test.txt"}
        result = get_unique_filename("test.txt", used_filenames)
        assert result == "test_1.txt"
        assert "test_1.txt" in used_filenames
        assert "test.txt" in used_filenames

    def test_unique_filename_multiple_conflicts(self):
        """Test that unique filenames are generated for multiple conflicts"""
        used_filenames = {"test.txt", "test_1.txt", "test_2.txt"}
        result = get_unique_filename("test.txt", used_filenames)
        assert result == "test_3.txt"
        assert "test_3.txt" in used_filenames

    def test_unique_filename_no_extension(self):
        """Test that unique filenames work correctly for files without extensions"""
        used_filenames = {"testfile"}
        result = get_unique_filename("testfile", used_filenames)
        assert result == "testfile_1"
        assert "testfile_1" in used_filenames

    def test_unique_filename_dot_file(self):
        """Test that unique filenames work correctly for dot files"""
        used_filenames = {".gitignore"}
        result = get_unique_filename(".gitignore", used_filenames)
        assert result == ".gitignore_1"
        assert ".gitignore_1" in used_filenames

    def test_unique_filename_multiple_dots(self):
        """Test that unique filenames work correctly for files with multiple dots"""
        used_filenames = {"test.backup.txt"}
        result = get_unique_filename("test.backup.txt", used_filenames)
        assert result == "test.backup_1.txt"
        assert "test.backup_1.txt" in used_filenames

    def test_unique_filename_preserves_used_filenames(self):
        """Test that the used_filenames set is properly maintained across calls"""
        used_filenames = set()

        # First call
        result1 = get_unique_filename("test.txt", used_filenames)
        assert result1 == "test.txt"
        assert used_filenames == {"test.txt"}

        # Second call with same filename
        result2 = get_unique_filename("test.txt", used_filenames)
        assert result2 == "test_1.txt"
        assert used_filenames == {"test.txt", "test_1.txt"}

        # Third call with different filename
        result3 = get_unique_filename("other.txt", used_filenames)
        assert result3 == "other.txt"
        assert used_filenames == {"test.txt", "test_1.txt", "other.txt"}

    def test_unique_filename_empty_string(self):
        """Test that empty filename is handled correctly"""
        used_filenames = set()
        result = get_unique_filename("", used_filenames)
        assert result == ""
        assert "" in used_filenames

    def test_unique_filename_unicode_characters(self):
        """Test that unicode characters in filenames are handled correctly"""
        used_filenames = {"测试.txt"}
        result = get_unique_filename("测试.txt", used_filenames)
        assert result == "测试_1.txt"
        assert "测试_1.txt" in used_filenames

    def test_unique_filename_special_characters(self):
        """Test that special characters in filenames are handled correctly"""
        used_filenames = {"test-file.txt"}
        result = get_unique_filename("test-file.txt", used_filenames)
        assert result == "test-file_1.txt"
        assert "test-file_1.txt" in used_filenames

    def test_unique_filename_long_filename(self):
        """Test that long filenames are handled correctly"""
        long_filename = "a" * 200 + ".txt"
        used_filenames = {long_filename}
        result = get_unique_filename(long_filename, used_filenames)
        expected = "a" * 200 + "_1.txt"
        assert result == expected
        assert expected in used_filenames

    def test_unique_filename_case_sensitivity(self):
        """Test that filename uniqueness is case-sensitive"""
        used_filenames = {"Test.txt"}
        result = get_unique_filename("test.txt", used_filenames)
        assert result == "test.txt"  # Should not conflict with "Test.txt"
        assert "test.txt" in used_filenames

    def test_unique_filename_gap_in_numbering(self):
        """Test that gaps in numbering are handled correctly"""
        used_filenames = {"test.txt", "test_1.txt", "test_3.txt"}
        result = get_unique_filename("test.txt", used_filenames)
        assert result == "test_2.txt"  # Should fill the gap
        assert "test_2.txt" in used_filenames

    def test_unique_filename_shared_used_filenames_set(self):
        """Test that multiple calls with the same used_filenames set work correctly"""
        used_filenames = set()

        # Simulate multiple files being processed
        files = ["report.pdf", "data.csv", "report.pdf", "summary.txt", "report.pdf"]
        expected_results = [
            "report.pdf",
            "data.csv",
            "report_1.pdf",
            "summary.txt",
            "report_2.pdf",
        ]

        for i, filename in enumerate(files):
            result = get_unique_filename(filename, used_filenames)
            assert result == expected_results[i]

        # Verify all expected filenames are in the set
        assert used_filenames == set(expected_results)
