import os
from typing import Optional

import pytest
from pytest import param

from fides.api.service.storage.util import (
    AllowedFileType,
    get_allowed_file_type_or_raise,
    get_local_filename,
    adaptive_chunk_size,
    should_split_package,
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


class TestAdaptiveChunkSize:
    """Tests for the adaptive_chunk_size function"""

    @pytest.mark.parametrize(
        "file_size, expected_chunk_size, description",
        [
            param(200 * 1024 * 1024, 1024 * 1024, "100MB+ file should use 1MB chunks", id="large_file_1mb_chunks"),
            param(150 * 1024 * 1024, 1024 * 1024, "150MB file should use 1MB chunks", id="150mb_file_1mb_chunks"),
            param(50 * 1024 * 1024, 256 * 1024, "50MB file should use 256KB chunks", id="50mb_file_256kb_chunks"),
            param(15 * 1024 * 1024, 256 * 1024, "15MB file should use 256KB chunks", id="15mb_file_256kb_chunks"),
            param(5 * 1024 * 1024, 128 * 1024, "5MB file should use 128KB chunks", id="5mb_file_128kb_chunks"),
            param(2 * 1024 * 1024, 128 * 1024, "2MB file should use 128KB chunks", id="2mb_file_128kb_chunks"),
            param(512 * 1024, 64 * 1024, "512KB file should use 64KB chunks", id="512kb_file_64kb_chunks"),
            param(100 * 1024, 64 * 1024, "100KB file should use 64KB chunks", id="100kb_file_64kb_chunks"),
            param(1024, 64 * 1024, "1KB file should use 64KB chunks", id="1kb_file_64kb_chunks"),
            param(0, 64 * 1024, "0 byte file should use 64KB chunks", id="0_byte_file_64kb_chunks"),
        ],
    )
    def test_adaptive_chunk_size_various_file_sizes(self, file_size, expected_chunk_size, description):
        """Test that adaptive_chunk_size returns appropriate chunk sizes for different file sizes"""
        result = adaptive_chunk_size(file_size)
        assert result == expected_chunk_size, f"Failed for {description}"

    def test_adaptive_chunk_size_edge_cases(self):
        """Test edge cases for adaptive_chunk_size function"""
        # Test exact boundary values (files exactly at boundary get smaller chunk size)
        assert adaptive_chunk_size(100 * 1024 * 1024) == 256 * 1024    # Exactly 100MB gets 256KB
        assert adaptive_chunk_size(10 * 1024 * 1024) == 128 * 1024     # Exactly 10MB gets 128KB
        assert adaptive_chunk_size(1 * 1024 * 1024) == 64 * 1024       # Exactly 1MB gets 64KB

        # Test values just below boundaries
        assert adaptive_chunk_size(99 * 1024 * 1024) == 256 * 1024    # Just below 100MB
        assert adaptive_chunk_size(9 * 1024 * 1024) == 128 * 1024     # Just below 10MB
        assert adaptive_chunk_size(999 * 1024) == 64 * 1024            # Just below 1MB

        # Test values just above boundaries with debug output
        result_101mb = adaptive_chunk_size(101 * 1024 * 1024)
        assert result_101mb == 1024 * 1024  # Just above 100MB

        result_11mb = adaptive_chunk_size(11 * 1024 * 1024)
        assert result_11mb == 256 * 1024    # Just above 10MB

        # Test a file just above 1MB (e.g., 1.1MB)
        result_1_1mb = adaptive_chunk_size(int(1.1 * 1024 * 1024))
        assert result_1_1mb == 128 * 1024   # Just above 1MB gets 128KB chunks

        result_1001kb = adaptive_chunk_size(1001 * 1024)
        assert result_1001kb == 64 * 1024   # 1001KB is less than 1MB, so gets 64KB chunks

    def test_adaptive_chunk_size_negative_values(self):
        """Test that adaptive_chunk_size handles negative values gracefully"""
        # For negative values, it should still return the smallest chunk size
        assert adaptive_chunk_size(-1) == 64 * 1024
        assert adaptive_chunk_size(-100 * 1024 * 1024) == 64 * 1024

    def test_adaptive_chunk_size_very_large_files(self):
        """Test that adaptive_chunk_size handles very large files"""
        # Test with extremely large file sizes
        assert adaptive_chunk_size(1 * 1024 * 1024 * 1024) == 1024 * 1024  # 1GB
        assert adaptive_chunk_size(10 * 1024 * 1024 * 1024) == 1024 * 1024  # 10GB
        assert adaptive_chunk_size(100 * 1024 * 1024 * 1024) == 1024 * 1024  # 100GB


class TestShouldSplitPackage:
    """Tests for the should_split_package function"""

    def test_should_split_package_by_attachment_count(self):
        """Test that packages are split when attachment count exceeds limit"""
        # Create data with more than 100 attachments
        data = {
            "users": [
                {"id": i, "attachments": [{"size": 1024, "s3_key": f"key_{i}_{j}"} for j in range(25)]}
                for i in range(5)  # 5 users * 25 attachments = 125 attachments
            ]
        }

        assert should_split_package(data, max_attachments=100) is True
        assert should_split_package(data, max_attachments=150) is False

    def test_should_split_package_by_size(self):
        """Test that packages are split when total size exceeds limit"""
        # Create data with more than 5GB estimated size
        data = {
            "documents": [
                {"id": i, "attachments": [{"size": 1024 * 1024 * 1024, "s3_key": f"key_{i}"}]}
                for i in range(6)  # 6 * 1GB = 6GB
            ]
        }

        assert should_split_package(data, max_total_size_gb=5) is True
        assert should_split_package(data, max_total_size_gb=10) is False

    def test_should_split_package_no_attachments(self):
        """Test that packages with no attachments are not split"""
        data = {
            "users": [
                {"id": 1, "name": "John"},
                {"id": 2, "name": "Jane"}
            ]
        }

        assert should_split_package(data) is False

    def test_should_split_package_empty_data(self):
        """Test that empty data is not split"""
        data = {}
        assert should_split_package(data) is False

    def test_should_split_package_mixed_data_types(self):
        """Test that packages with mixed data types are handled correctly"""
        data = {
            "users": [
                {"id": 1, "attachments": [{"size": 1024, "s3_key": "key1"}]},
                {"id": 2, "attachments": [{"size": 1024, "s3_key": "key2"}]}
            ],
            "metadata": {"total": 2},  # Non-list value
            "documents": [
                {"id": 3, "attachments": [{"size": 1024, "s3_key": "key3"}]}
            ]
        }

        # Should not split with default limits
        assert should_split_package(data) is False

        # Should split with very low limits
        assert should_split_package(data, max_attachments=2, max_total_size_gb=0.001) is True

    def test_should_split_package_custom_limits(self):
        """Test that custom limits are respected"""
        data = {
            "files": [
                {"id": i, "attachments": [{"size": 1024, "s3_key": f"key_{i}"}]}
                for i in range(50)
            ]
        }

        # Test custom attachment limit
        assert should_split_package(data, max_attachments=25) is True
        assert should_split_package(data, max_attachments=100) is False

        # Test custom size limit - 50 files * 1KB = 50KB, which is less than 0.001GB (1MB)
        # So it should NOT split
        result = should_split_package(data, max_total_size_gb=0.001)
        assert result is False

    def test_should_split_package_missing_size_estimation(self):
        """Test that missing size information uses default estimation"""
        data = {
            "files": [
                {"id": i, "attachments": [{"s3_key": f"key_{i}"}]}  # No size field
                for i in range(1000)  # 1000 * 1MB default = 1GB
            ]
        }

        # Should split with default 100 attachment limit (1000 > 100)
        result = should_split_package(data)
        assert result is True

        # Should not split with higher attachment limit
        result_high_limit = should_split_package(data, max_attachments=2000)
        assert result_high_limit is False

        # Should split with lower size limit
        result_low_size = should_split_package(data, max_total_size_gb=0.5)
        assert result_low_size is True

    def test_should_split_package_nested_structures(self):
        """Test that nested data structures are handled correctly"""
        data = {
            "departments": [
                {
                    "name": "Engineering",
                    "employees": [
                        {
                            "id": i,
                            "attachments": [{"size": 1024, "s3_key": f"eng_key_{i}_{j}"} for j in range(10)]
                        }
                        for i in range(10)  # 10 employees * 10 attachments = 100 attachments
                    ]
                }
            ]
        }

        # Should not split with default 100 attachment limit
        assert should_split_package(data) is False

        # Should split with 50 attachment limit
        assert should_split_package(data, max_attachments=50) is True

    def test_should_split_package_edge_cases(self):
        """Test edge cases for should_split_package function"""
        # Test with exactly at the limit
        data = {
            "files": [
                {"id": i, "attachments": [{"size": 1024, "s3_key": f"key_{i}"}]}
                for i in range(100)  # Exactly 100 attachments
            ]
        }

        # Should not split when exactly at the limit
        assert should_split_package(data, max_attachments=100) is False

        # Should split when over the limit
        assert should_split_package(data, max_attachments=99) is True

        # Test with exactly at size limit
        data = {
            "files": [
                {"id": i, "attachments": [{"size": 1024 * 1024 * 1024, "s3_key": f"key_{i}"}]}
                for i in range(5)  # Exactly 5GB
            ]
        }

        # Should not split when exactly at the size limit
        assert should_split_package(data, max_total_size_gb=5) is False

        # Should split when over the size limit
        assert should_split_package(data, max_total_size_gb=4) is True
