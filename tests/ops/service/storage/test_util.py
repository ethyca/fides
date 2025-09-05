import os
from typing import Optional

import pytest
from pytest import param

from fides.api.service.storage.util import (
    AllowedFileType,
    get_allowed_file_type_or_raise,
    get_local_filename,
    get_unique_filename,
    resolve_base_path_from_context,
    resolve_directory_from_context,
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

    @pytest.mark.parametrize(
        "filename, used_filenames, expected_result",
        [
            param("test.txt", set(), "test.txt", id="no_conflict"),
            param("test.txt", {"test.txt"}, "test_1.txt", id="with_conflict"),
            param(
                "test.txt",
                {"test.txt", "test_1.txt"},
                "test_2.txt",
                id="multiple_conflicts",
            ),
            param(
                "test.txt",
                {"test.txt", "test_1.txt", "test_2.txt"},
                "test_3.txt",
                id="multiple_conflicts_3",
            ),
            param("testfile", set(), "testfile", id="no_conflict_with_file"),
            param(".testfile", set(), ".testfile", id="no_conflict_with_dot_file"),
            param(
                "test.backup.txt",
                set(),
                "test.backup.txt",
                id="no_conflict_with_multiple_dots",
            ),
            param(
                "测试.txt",
                set(),
                "测试.txt",
                id="no_conflict_with_unicode_characters",
            ),
            param("test-file.txt", set(), "test-file.txt", id="no_conflict_with_dash"),
            param(
                "a" * 200 + ".txt",
                set(),
                "a" * 200 + ".txt",
                id="no_conflict_with_long_filename",
            ),
            param(
                "Test.txt", set(), "Test.txt", id="no_conflict_with_case_sensitivity"
            ),
            param(
                "test.txt",
                {"test.txt", "test_1.txt", "test_3.txt"},
                "test_2.txt",
                id="multiple_conflicts_with_used_filenames",
            ),
        ],
    )
    def test_unique_filename_no_conflict(
        self, filename, used_filenames, expected_result
    ):
        """Test that a unique filename is returned when no conflicts exist"""
        result = get_unique_filename(filename, used_filenames)
        assert result == expected_result


class TestExtractStorageKeyFromAttachment:
    """Tests for the extract_storage_key_from_attachment function"""

    @pytest.mark.parametrize(
        "attachment, expected_key",
        [
            param(
                {"original_download_url": "https://example.com/file.pdf"},
                "https://example.com/file.pdf",
                id="original_download_url_only",
            ),
            param(
                {
                    "original_download_url": "https://example.com/file.pdf",
                    "download_url": "https://backup.com/file.pdf",
                },
                "https://example.com/file.pdf",
                id="original_download_url_priority",
            ),
            param(
                {"download_url": "https://example.com/file.pdf"},
                "https://example.com/file.pdf",
                id="download_url_only",
            ),
            param(
                {
                    "download_url": "https://example.com/file.pdf",
                    "file_name": "backup.pdf",
                },
                "https://example.com/file.pdf",
                id="download_url_priority_over_filename",
            ),
            param(
                {"file_name": "document.pdf"},
                "document.pdf",
                id="file_name_only",
            ),
            param(
                {
                    "original_download_url": "",
                    "download_url": "",
                    "file_name": "document.pdf",
                },
                "document.pdf",
                id="empty_urls_fallback_to_filename",
            ),
            param(
                {
                    "original_download_url": None,
                    "download_url": None,
                    "file_name": "document.pdf",
                },
                "document.pdf",
                id="none_urls_fallback_to_filename",
            ),
            param(
                {
                    "original_download_url": "",
                    "download_url": "",
                    "file_name": "",
                },
                "",
                id="all_empty_returns_empty",
            ),
            param(
                {
                    "original_download_url": None,
                    "download_url": None,
                    "file_name": None,
                },
                "",
                id="all_none_returns_empty",
            ),
            param(
                {
                    "original_download_url": "s3://bucket/path/file.pdf",
                    "download_url": "https://example.com/file.pdf",
                    "file_name": "document.pdf",
                },
                "s3://bucket/path/file.pdf",
                id="s3_url_priority",
            ),
        ],
    )
    def test_extract_storage_key(self, attachment, expected_key):
        """Test that storage key is extracted correctly with proper fallback logic"""
        result = extract_storage_key_from_attachment(attachment)
        assert result == expected_key

    def test_extract_storage_key_missing_keys(self):
        """Test that missing keys are handled gracefully"""
        result = extract_storage_key_from_attachment({})
        assert result == ""

    def test_extract_storage_key_with_extra_keys(self):
        """Test that extra keys in attachment don't interfere"""
        attachment = {
            "original_download_url": "https://example.com/file.pdf",
            "download_url": "https://backup.com/file.pdf",
            "file_name": "document.pdf",
            "extra_field": "should_be_ignored",
            "size": 1024,
        }
        result = extract_storage_key_from_attachment(attachment)
        assert result == "https://example.com/file.pdf"


class TestGenerateAttachmentUrlFromStoragePath:
    """Tests for the generate_attachment_url_from_storage_path function"""

    def test_generate_attachment_url_streaming_mode_same_directory(self):
        """Test URL generation in streaming mode for same directory."""
        from fides.api.service.storage.util import (
            generate_attachment_url_from_storage_path,
        )

        result = generate_attachment_url_from_storage_path(
            download_url="https://example.com/file.pdf",
            unique_filename="test file % pdf.pdf",
            base_path="attachments",
            html_directory="attachments",
            enable_streaming=True,
        )

        # Should URL-encode the filename
        assert result == "test%20file%20%25%20pdf.pdf"

    def test_generate_attachment_url_streaming_mode_data_directory(self):
        """Test URL generation in streaming mode for data directory."""
        from fides.api.service.storage.util import (
            generate_attachment_url_from_storage_path,
        )

        result = generate_attachment_url_from_storage_path(
            download_url="https://example.com/file.pdf",
            unique_filename="test file % pdf.pdf",
            base_path="data/dataset/collection",
            html_directory="data/dataset/collection",
            enable_streaming=True,
        )

        # Should URL-encode the filename and add attachments prefix
        assert result == "attachments/test%20file%20%25%20pdf.pdf"

    def test_generate_attachment_url_streaming_mode_other_cases(self):
        """Test URL generation in streaming mode for other cases."""
        from fides.api.service.storage.util import (
            generate_attachment_url_from_storage_path,
        )

        result = generate_attachment_url_from_storage_path(
            download_url="https://example.com/file.pdf",
            unique_filename="test file % pdf.pdf",
            base_path="other/path",
            html_directory="different/path",
            enable_streaming=True,
        )

        # Should URL-encode the filename in the relative path
        assert result == "../other/path/test%20file%20%25%20pdf.pdf"

    def test_generate_attachment_url_non_streaming_mode(self):
        """Test URL generation in non-streaming mode."""
        from fides.api.service.storage.util import (
            generate_attachment_url_from_storage_path,
        )

        result = generate_attachment_url_from_storage_path(
            download_url="https://example.com/file.pdf",
            unique_filename="test file % pdf.pdf",
            base_path="attachments",
            html_directory="attachments",
            enable_streaming=False,
        )

        # Should return the original download URL
        assert result == "https://example.com/file.pdf"

    def test_generate_attachment_url_special_characters(self):
        """Test URL generation with various special characters."""
        from fides.api.service.storage.util import (
            generate_attachment_url_from_storage_path,
        )

        test_cases = [
            ("file with spaces.pdf", "file%20with%20spaces.pdf"),
            ("file%20with%20encoded.pdf", "file%2520with%2520encoded.pdf"),
            ("file+with+plus.pdf", "file%2Bwith%2Bplus.pdf"),
            ("file#with#hash.pdf", "file%23with%23hash.pdf"),
            ("file?with?query.pdf", "file%3Fwith%3Fquery.pdf"),
            ("file&with&ampersand.pdf", "file%26with%26ampersand.pdf"),
        ]

        for filename, expected_encoded in test_cases:
            result = generate_attachment_url_from_storage_path(
                download_url="https://example.com/file.pdf",
                unique_filename=filename,
                base_path="attachments",
                html_directory="attachments",
                enable_streaming=True,
            )
            assert result == expected_encoded, f"Failed for filename: {filename}"


class TestResolveBasePathFromContext:
    """Tests for the resolve_base_path_from_context function"""

    @pytest.mark.parametrize(
        "attachment, default_base_path, expected_path",
        [
            param(
                {
                    "_context": {
                        "type": "direct",
                        "dataset": "users",
                        "collection": "profiles",
                    }
                },
                "attachments",
                "data/users/profiles/attachments",
                id="direct_context",
            ),
            param(
                {
                    "_context": {
                        "type": "nested",
                        "dataset": "orders",
                        "collection": "items",
                    }
                },
                "attachments",
                "data/orders/items/attachments",
                id="nested_context",
            ),
            param(
                {"_context": {"type": "top_level"}},
                "attachments",
                "attachments",
                id="top_level_context",
            ),
            param(
                {
                    "_context": {
                        "type": "old_format",
                        "key": "dataset:collection",
                        "item_id": "123",
                    }
                },
                "attachments",
                "dataset:collection/123/attachments",
                id="old_context_format",
            ),
            param(
                {},  # no context
                "attachments",
                "attachments",
                id="no_context_default",
            ),
            param(
                {},  # no context with custom default
                "custom/path",
                "custom/path",
                id="no_context_custom_default",
            ),
            param(
                {"_context": {}},  # empty context
                "attachments",
                "attachments",
                id="empty_context",
            ),
            param(
                {
                    "_context": {
                        "type": "direct",
                        "dataset": "users",
                        "collection": "profiles",
                    }
                },
                "custom/default",
                "data/users/profiles/attachments",
                id="context_overrides_default",
            ),
        ],
    )
    def test_resolve_base_path(self, attachment, default_base_path, expected_path):
        """Test that base path is resolved correctly based on context"""
        result = resolve_base_path_from_context(attachment, default_base_path)
        assert result == expected_path

    def test_resolve_base_path_with_none_context(self):
        """Test that None context is handled gracefully"""
        attachment = {"_context": None}
        result = resolve_base_path_from_context(attachment, "default")
        assert result == "default"


class TestResolveDirectoryFromContext:
    """Tests for the resolve_directory_from_context function"""

    @pytest.mark.parametrize(
        "attachment, default_directory, expected_directory",
        [
            param(
                {
                    "_context": {
                        "type": "direct",
                        "dataset": "users",
                        "collection": "profiles",
                    }
                },
                "attachments",
                "data/users/profiles",
                id="direct_context",
            ),
            param(
                {
                    "_context": {
                        "type": "nested",
                        "dataset": "orders",
                        "collection": "items",
                    }
                },
                "attachments",
                "data/orders/items",
                id="nested_context",
            ),
            param(
                {"_context": {"type": "top_level"}},
                "attachments",
                "attachments",
                id="top_level_context",
            ),
            param(
                {
                    "_context": {
                        "type": "old_format",
                        "key": "dataset:collection",
                        "item_id": "123",
                    }
                },
                "attachments",
                "dataset:collection/123",
                id="old_context_format",
            ),
            param(
                {},  # no context
                "attachments",
                "attachments",
                id="no_context_default",
            ),
            param(
                {},  # no context with custom default
                "custom/path",
                "custom/path",
                id="no_context_custom_default",
            ),
            param(
                {"_context": {}},  # empty context
                "attachments",
                "attachments",
                id="empty_context",
            ),
            param(
                {
                    "_context": {
                        "type": "direct",
                        "dataset": "users",
                        "collection": "profiles",
                    }
                },
                "custom/default",
                "data/users/profiles",
                id="context_overrides_default",
            ),
            param(
                {
                    "_context": {"key": "dataset:collection", "item_id": "123"}
                },  # old format without type
                "attachments",
                "dataset:collection/123",
                id="old_format_without_type",
            ),
            param(
                {
                    "_context": {"key": "dataset:collection"}
                },  # old format missing item_id
                "attachments",
                "attachments",
                id="old_format_missing_item_id",
            ),
        ],
    )
    def test_resolve_directory(self, attachment, default_directory, expected_directory):
        """Test that directory is resolved correctly based on context"""
        result = resolve_directory_from_context(attachment, default_directory)
        assert result == expected_directory

    def test_resolve_directory_with_none_context(self):
        """Test that None context is handled gracefully"""
        attachment = {"_context": None}
        result = resolve_directory_from_context(attachment, "default")
        assert result == "default"
