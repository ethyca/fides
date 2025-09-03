import io
import zipfile

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import DsrReportBuilder

from .conftest import TestDsrReportBuilderBase


class TestDsrReportBuilderAttachments(TestDsrReportBuilderBase):
    """Tests for attachment handling in DSR reports"""

    def test_webhook_attachments(
        self,
        privacy_request: PrivacyRequest,
        webhook_variants,
        common_assertions,
        common_attachment_config,
    ):
        """Test handling of attachments in webhook data"""
        dsr_data = {
            "test_webhook": [webhook_variants["basic"]],
            "attachments": [
                common_attachment_config["text"],
                common_attachment_config["binary"],
            ],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify that the attachments index file exists
            self.assert_file_in_zip(
                zip_file, f"{common_assertions['paths']['attachments_dir']}/index.html"
            )

            # Read and verify the content of the attachments index file
            attachments_content = zip_file.read(
                f"{common_assertions['paths']['attachments_dir']}/index.html"
            ).decode("utf-8")

            # Verify both attachment links are present with their details
            self.assert_html_contains(
                attachments_content,
                common_attachment_config["text"]["file_name"],
                common_attachment_config["text"]["download_url"],
                "1.0 KB",  # Assuming the file size is formatted as 1.0 KB
            )
            self.assert_html_contains(
                attachments_content,
                common_attachment_config["binary"]["file_name"],
                common_attachment_config["binary"]["download_url"],
                "2.0 KB",  # Assuming the file size is formatted as 2.0 KB
            )

    def test_streaming_attachment_links(
        self,
        privacy_request: PrivacyRequest,
        common_attachment_config,
        common_assertions,
    ):
        """Test that when streaming is enabled, attachment links point to local attachments directory"""
        dsr_data = {
            "attachments": [
                common_attachment_config["text"],
                common_attachment_config["binary"],
            ],
        }

        # Test with streaming enabled
        builder_streaming = DsrReportBuilder(
            privacy_request=privacy_request, dsr_data=dsr_data, enable_streaming=True
        )
        report_streaming = builder_streaming.generate()

        with zipfile.ZipFile(io.BytesIO(report_streaming.getvalue())) as zip_file:
            # Read the attachments index file
            attachments_content = zip_file.read(
                f"{common_assertions['paths']['attachments_dir']}/index.html"
            ).decode("utf-8")

            # Verify that links point to local attachments directory
            self.assert_html_contains(
                attachments_content,
                common_attachment_config["text"]["file_name"],
                common_attachment_config["text"][
                    "file_name"
                ],  # Just filename, not full path
                "1.0 KB",
            )
            self.assert_html_contains(
                attachments_content,
                common_attachment_config["binary"]["file_name"],
                common_attachment_config["binary"][
                    "file_name"
                ],  # Just filename, not full path
                "2.0 KB",
            )

            # Verify that original download URLs are NOT present
            self.assert_html_not_contains(
                attachments_content,
                common_attachment_config["text"]["download_url"],
                common_attachment_config["binary"]["download_url"],
            )

        # Test with streaming disabled (default behavior)
        builder_default = DsrReportBuilder(
            privacy_request=privacy_request, dsr_data=dsr_data, enable_streaming=False
        )
        report_default = builder_default.generate()

        with zipfile.ZipFile(io.BytesIO(report_default.getvalue())) as zip_file:
            # Read the attachments index file
            attachments_content = zip_file.read(
                f"{common_assertions['paths']['attachments_dir']}/index.html"
            ).decode("utf-8")

            # Verify that links point to original download URLs
            self.assert_html_contains(
                attachments_content,
                common_attachment_config["text"]["file_name"],
                common_attachment_config["text"]["download_url"],
                "1.0 KB",
            )
            self.assert_html_contains(
                attachments_content,
                common_attachment_config["binary"]["file_name"],
                common_attachment_config["binary"]["download_url"],
                "2.0 KB",
            )

    def test_ttl_display_in_templates(
        self,
        privacy_request: PrivacyRequest,
        common_attachment_config,
        common_assertions,
    ):
        """Test that TTL is displayed correctly in templates using the environment variable"""
        dsr_data = {
            "attachments": [
                common_attachment_config["text"],
            ],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Read the attachments index file
            attachments_content = zip_file.read(
                f"{common_assertions['paths']['attachments_dir']}/index.html"
            ).decode("utf-8")

            # Verify that the TTL is displayed (should be 5 days by default)
            # The exact number will depend on the CONFIG.security.subject_request_download_link_ttl_seconds value
            self.assert_html_contains(
                attachments_content, "download links will expire in"
            )
            self.assert_html_contains(attachments_content, "days")

            # Verify that the hardcoded "7 days" is not present
            self.assert_html_not_contains(attachments_content, "7 days")

    def test_ttl_display_in_collection_templates(
        self,
        privacy_request: PrivacyRequest,
        common_assertions,
    ):
        """Test that TTL is displayed correctly in collection templates using the environment variable"""
        dsr_data = {
            "test_dataset:test_collection": [
                {
                    "id": 1,
                    "name": "Test Item",
                    "attachments": {
                        "test_file.txt": {
                            "url": "https://example.com/test_file.txt",
                            "size": "1.0 KB",
                        }
                    },
                }
            ]
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Read the collection index file
            collection_content = zip_file.read(
                "data/test_dataset/test_collection/index.html"
            ).decode("utf-8")

            # Verify that the TTL is displayed
            self.assert_html_contains(
                collection_content, "download links will expire in"
            )
            self.assert_html_contains(collection_content, "days")

            # Verify that the hardcoded "7 days" is not present
            self.assert_html_not_contains(collection_content, "7 days")

    def test_multiple_webhook_attachments(
        self, privacy_request: PrivacyRequest, webhook_variants, common_assertions
    ):
        """Test handling of attachments across multiple webhooks"""
        dsr_data = {
            "test_webhook": [
                {
                    **webhook_variants["basic"],
                    "attachments": [
                        webhook_variants["with_attachments"]["attachments"][0]
                    ],
                }
            ],
            "test_webhook2": [
                {
                    "phone": webhook_variants["basic"]["phone"],
                    "attachments": [
                        webhook_variants["with_attachments"]["attachments"][1]
                    ],
                    "system_name": "test_system2",
                }
            ],
            "attachments": [webhook_variants["with_attachments"]["attachments"][0]],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify that webhook index files exist
            self.assert_file_in_zip(
                zip_file, f"{common_assertions['paths']['webhook_dir']}/index.html"
            )
            self.assert_file_in_zip(
                zip_file, f"{common_assertions['paths']['webhook_dir2']}/index.html"
            )

            # Read and verify the content of the webhook index files
            webhook1_content = zip_file.read(
                f"{common_assertions['paths']['webhook_dir']}/index.html"
            ).decode("utf-8")
            webhook2_content = zip_file.read(
                f"{common_assertions['paths']['webhook_dir2']}/index.html"
            ).decode("utf-8")

            # Verify attachment links in webhook1
            self.assert_html_contains(
                webhook1_content,
                webhook_variants["with_attachments"]["attachments"][0]["file_name"],
                webhook_variants["with_attachments"]["attachments"][0]["download_url"],
                "1.0 KB",  # Assuming the file size is formatted as 1.0 KB
            )

            # Verify attachment links in webhook2
            self.assert_html_contains(
                webhook2_content,
                webhook_variants["with_attachments"]["attachments"][1]["file_name"],
                webhook_variants["with_attachments"]["attachments"][1]["download_url"],
                "2.0 KB",  # Assuming the file size is formatted as 2.0 KB
            )

    @pytest.mark.parametrize("webhook_type", ["empty_attachments", "malformed"])
    def test_webhook_variants(
        self,
        privacy_request: PrivacyRequest,
        webhook_variants,
        common_assertions,
        webhook_type,
    ):
        """Test different webhook data variants"""
        dsr_data = {
            "manual:test_webhook": [webhook_variants[webhook_type]],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify that the report was still generated
            self.assert_file_in_zip(
                zip_file,
                f"{common_assertions['paths']['manual_webhook_dir']}/index.html",
            )
            manual_data = zip_file.read(
                f"{common_assertions['paths']['manual_webhook_dir']}/index.html"
            ).decode("utf-8")
            self.assert_html_contains(
                manual_data, webhook_variants[webhook_type]["email"]
            )

            # Verify that attachments directory exists but contains no actual attachment files
            # (only the index.html file should be present)
            attachment_files = [
                name
                for name in zip_file.namelist()
                if name.startswith(f"{common_assertions['paths']['attachments_dir']}/")
            ]
            # Should only have the index.html file, no actual attachment files
            assert len(attachment_files) == 1
            assert (
                attachment_files[0]
                == f"{common_assertions['paths']['attachments_dir']}/index.html"
            )

            # Verify that the attachments index page exists and is accessible
            self.assert_file_in_zip(
                zip_file, f"{common_assertions['paths']['attachments_dir']}/index.html"
            )


class TestDsrReportBuilderAttachmentHandling:
    """Tests for DSR report builder's attachment handling functions"""

    def test_handle_attachment_text(self, privacy_request: PrivacyRequest):
        """Test handling of text attachments with download URLs"""
        builder = DsrReportBuilder(privacy_request, {})
        attachments = [
            {
                "file_name": "test.txt",
                "download_url": "https://example.com/test.txt",
                "file_size": 1024,
            }
        ]

        result = builder._write_attachment_content(attachments, "attachments")

        assert "test.txt" in result
        assert result["test.txt"]["url"] == "https://example.com/test.txt"
        assert result["test.txt"]["size"] == "1.0 KB"

    def test_handle_attachment_binary(self, privacy_request: PrivacyRequest):
        """Test handling of binary attachments with download URLs"""
        builder = DsrReportBuilder(privacy_request, {})
        attachments = [
            {
                "file_name": "test.pdf",
                "download_url": "https://example.com/test.pdf",
                "file_size": 2048576,  # 2MB
            }
        ]

        result = builder._write_attachment_content(attachments, "attachments")

        assert "test.pdf" in result
        assert result["test.pdf"]["url"] == "https://example.com/test.pdf"
        assert result["test.pdf"]["size"] == "2.0 MB"

    def test_handle_attachment_no_content(self, privacy_request: PrivacyRequest):
        """Test handling of attachments with missing content"""
        builder = DsrReportBuilder(privacy_request, {})
        attachments = [
            {"file_name": "test.txt", "download_url": None, "file_size": None}
        ]

        result = builder._write_attachment_content(attachments, "attachments")
        assert not result  # Should return empty dict for invalid attachments

    def test_add_attachments_top_level(self, privacy_request: PrivacyRequest):
        """Test adding top-level attachments to the report"""
        attachments = [
            {
                "file_name": "test1.txt",
                "download_url": "https://example.com/test1.txt",
                "file_size": 1024,
            },
            {
                "file_name": "test2.pdf",
                "download_url": "https://example.com/test2.pdf",
                "file_size": 2048576,
            },
        ]

        dsr_data = {"attachments": attachments}
        builder = DsrReportBuilder(privacy_request, dsr_data)
        zip_file = builder.generate()

        # Create a ZipFile object from the BytesIO
        with zipfile.ZipFile(zip_file) as zip_file_obj:
            # Check that attachments index was created
            TestDsrReportBuilderBase.assert_file_in_zip(
                zip_file_obj, "attachments/index.html"
            )

            # Check that the HTML contains the attachment links
            html_content = zip_file_obj.read("attachments/index.html").decode("utf-8")
            TestDsrReportBuilderBase.assert_html_contains(
                html_content,
                "test1.txt",
                "test2.pdf",
                "https://example.com/test1.txt",
                "https://example.com/test2.pdf",
                "1.0 KB",
                "2.0 MB",
            )

    def test_process_item_attachments(self, privacy_request: PrivacyRequest):
        """Test processing attachments within collection items"""
        dsr_data = {
            "dataset1:collection1": [
                {
                    "id": 1,
                    "name": "Item 1",
                    "attachments": [
                        {
                            "file_name": "item1.txt",
                            "download_url": "https://example.com/item1.txt",
                            "file_size": 1024,
                        }
                    ],
                }
            ]
        }

        builder = DsrReportBuilder(privacy_request, dsr_data)
        zip_file = builder.generate()

        # Create a ZipFile object from the BytesIO
        with zipfile.ZipFile(zip_file) as zip_file_obj:
            # Check that collection index was created
            TestDsrReportBuilderBase.assert_file_in_zip(
                zip_file_obj, "data/dataset1/collection1/index.html"
            )

            # Check that the HTML contains the attachment link
            html_content = zip_file_obj.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            TestDsrReportBuilderBase.assert_html_contains(
                html_content, "item1.txt", "https://example.com/item1.txt", "1.0 KB"
            )

    def test_handle_duplicate_filenames(self, privacy_request: PrivacyRequest):
        """Test handling of duplicate filenames across all directories"""
        builder = DsrReportBuilder(privacy_request, {})
        attachments = [
            {
                "file_name": "test.txt",
                "download_url": "https://example.com/test1.txt",
                "file_size": 1024,
            },
            {
                "file_name": "test.txt",
                "download_url": "https://example.com/test2.txt",
                "file_size": 2048,
            },
            {
                "file_name": "test.txt",
                "download_url": "https://example.com/test3.txt",
                "file_size": 3072,
            },
        ]

        result = builder._write_attachment_content(attachments, "attachments")

        # Verify that all files get unique names
        assert "test.txt" in result  # First file keeps original name
        assert "test_1.txt" in result  # Second file gets _1 suffix
        assert "test_2.txt" in result  # Third file gets _2 suffix
        assert result["test.txt"]["url"] == "https://example.com/test1.txt"
        assert result["test_1.txt"]["url"] == "https://example.com/test2.txt"
        assert result["test_2.txt"]["url"] == "https://example.com/test3.txt"

    def test_handle_duplicate_filenames_across_directories(
        self, privacy_request: PrivacyRequest
    ):
        """Test handling of duplicate filenames across different directories"""
        builder = DsrReportBuilder(privacy_request, {})

        # Test attachments in different directories
        attachments1 = [
            {
                "file_name": "test.txt",
                "download_url": "https://example.com/test1.txt",
                "file_size": 1024,
            }
        ]
        attachments2 = [
            {
                "file_name": "test.txt",
                "download_url": "https://example.com/test2.txt",
                "file_size": 2048,
            }
        ]

        # Process attachments in sequence
        result1 = builder._write_attachment_content(attachments1, "attachments")
        result2 = builder._write_attachment_content(
            attachments2, "data/dataset1/collection1"
        )

        # Verify that the second file gets a unique name
        assert "test.txt" in result1  # First file keeps original name
        assert "test_1.txt" in result2  # Second file gets _1 suffix
        assert result1["test.txt"]["url"] == "https://example.com/test1.txt"
        assert result2["test_1.txt"]["url"] == "https://example.com/test2.txt"


class TestDsrReportBuilderAttachmentContentWriting:
    """Tests for DSR report builder's attachment content writing functionality"""

    @pytest.mark.parametrize(
        "file_name,download_url,file_size,expected_size",
        [
            ("test.txt", "https://example.com/test.txt", 1024, "1.0 KB"),
            ("test.pdf", "https://example.com/test.pdf", 2048576, "2.0 MB"),
            ("test.txt", "https://example.com/test.txt", None, "Unknown"),
        ],
    )
    def test_write_attachment_content_parametrized(
        self,
        privacy_request: PrivacyRequest,
        file_name,
        download_url,
        file_size,
        expected_size,
    ):
        """Test attachment content writing with various file types and sizes"""
        builder = DsrReportBuilder(privacy_request, {})
        attachments = [
            {
                "file_name": file_name,
                "download_url": download_url,
                "file_size": file_size,
            }
        ]

        result = builder._write_attachment_content(attachments, "attachments")

        assert file_name in result
        assert result[file_name]["url"] == download_url
        assert result[file_name]["size"] == expected_size

    @pytest.mark.parametrize(
        "file_name,download_url,file_size,expected_size",
        [
            ("test.txt", None, 1024, None),  # Missing URL should be invalid
            (
                "test.pdf",
                "https://example.com/test.pdf",
                None,
                "Unknown",
            ),  # Missing size is valid
            (
                None,
                "https://example.com/test.txt",
                1024,
                None,
            ),  # Missing filename should be invalid
        ],
    )
    def test_write_attachment_content_no_content_parametrized(
        self,
        privacy_request: PrivacyRequest,
        file_name,
        download_url,
        file_size,
        expected_size,
    ):
        """Test attachment content writing with missing required fields"""
        builder = DsrReportBuilder(privacy_request, {})
        attachments = [
            {
                "file_name": file_name,
                "download_url": download_url,
                "file_size": file_size,
            }
        ]

        result = builder._write_attachment_content(attachments, "attachments")

        if expected_size is None:
            # Should return empty dict for invalid attachments (missing filename or URL)
            assert not result
        else:
            # Should include attachment with missing size
            assert file_name in result
            assert result[file_name]["url"] == download_url
            assert result[file_name]["size"] == expected_size

    @pytest.mark.parametrize("directory", ["attachments", "data/dataset1/collection1"])
    def test_write_attachment_content_different_directories_parametrized(
        self, privacy_request: PrivacyRequest, directory
    ):
        """Test attachment content writing in different directories"""
        builder = DsrReportBuilder(privacy_request, {})
        attachments = [
            {
                "file_name": "test.txt",
                "download_url": "https://example.com/test.txt",
                "file_size": 1024,
            }
        ]

        result = builder._write_attachment_content(attachments, directory)

        assert "test.txt" in result
        assert result["test.txt"]["url"] == "https://example.com/test.txt"
        assert result["test.txt"]["size"] == "1.0 KB"



class TestDSRReportBuilderDuplicateFileNames:
    """Tests for handling files with same names but different URLs in the DSR report"""

    @pytest.mark.parametrize("enable_streaming", [True, False])
    def test_duplicate_file_names(self, storage_config, privacy_request: PrivacyRequest, enable_streaming, dsr_data_duplicate_file_names):
        """Test that collection-specific and global attachment indexes correctly handle files with same names but different URLs

        Expected DSR Report Structure:
        ├── data/manualtask/manual_data/index.html (collection-specific: 1 text file)
        ├── data/manualtask2/manual_data/index.html (collection-specific: 1 PDF + 2 text files)
        └── attachments/index.html (global index: all 4 attachments)

        Note: Each attachment appears twice in HTML (filename display + URL), so filename counts are doubled.
        """

        storage_config.details["enable_streaming"] = enable_streaming
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data_duplicate_file_names)
        report = builder.generate()
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Get all file names in the zip
            all_files = zip_file.namelist()

            # Verify the expected HTML structure is present
            expected_html_files = [
                "welcome.html",
                "data/manualtask/index.html",
                "data/manualtask/manual_data/index.html",
                "data/manualtask2/index.html",
                "data/manualtask2/manual_data/index.html",
                "attachments/index.html"
            ]

            for expected_html in expected_html_files:
                assert expected_html in all_files, f"Expected HTML file {expected_html} not found in zip. Available files: {all_files}"

            # 1. Verify dataset-specific collection indexes contain the correct attachments
            # Check manualtask dataset collection
            manualtask_collection_html = zip_file.read("data/manualtask/manual_data/index.html").decode('utf-8')
            assert "test_file_text.txt" in manualtask_collection_html, "manualtask should have test_file_text.txt"

            # Check manualtask2 dataset collection
            manualtask2_collection_html = zip_file.read("data/manualtask2/manual_data/index.html").decode('utf-8')
            # manualtask2 has 3 files: 1 PDF + 2 text files with same name but different URLs
            # Since they have different URLs, they should keep original names (not incremented)
            assert "test_file_pdf.pdf" in manualtask2_collection_html, "manualtask2 should have test_file_pdf.pdf"
            assert "test_file_text.txt" in manualtask2_collection_html, "manualtask2 should have test_file_text.txt"

            # Verify that each dataset collection shows its own attachments
            # manualtask should only show its 1 text file
            manualtask_text_count = manualtask_collection_html.count("test_file_text.txt")
            assert manualtask_text_count >= 1, f"manualtask should show at least 1 test_file_text.txt, found {manualtask_text_count}"

            # manualtask2 should show its 3 files (1 PDF + 2 text files)
            manualtask2_text_count = manualtask2_collection_html.count("test_file_text.txt")
            manualtask2_pdf_count = manualtask2_collection_html.count("test_file_pdf.pdf")
            assert manualtask2_text_count >= 2, f"manualtask2 should show at least 2 test_file_text.txt files, found {manualtask2_text_count}"
            assert manualtask2_pdf_count >= 1, f"manualtask2 should show at least 1 test_file_pdf.pdf, found {manualtask2_pdf_count}"

            # 2. Verify global attachments index shows all attachments with dataset paths
            attachments_html = zip_file.read("attachments/index.html").decode('utf-8')

            # Verify all expected filenames are present in the global attachments index
            expected_filenames = [
                "test_file_text.txt",      # From manualtask (1 occurrence)
                "test_file_text.txt",      # From manualtask2 (2 occurrences, same name different URLs)
                "test_file_pdf.pdf"        # From manualtask2 (1 occurrence)
            ]

            for expected_filename in expected_filenames:
                assert expected_filename in attachments_html, f"Expected filename {expected_filename} not found in global attachments index"

            # Verify total counts in global attachments index
            # Each attachment appears twice in the HTML (filename display + URL), so we need to count table rows
            # Count the number of attachment table rows (each row represents one attachment)
            attachment_rows = attachments_html.count('class="table-row" target="_blank"')
            assert attachment_rows == 4, f"Global attachments should have 4 total attachment rows, found {attachment_rows}"

            # Verify that test_file_text.txt appears in the expected number of attachment entries
            # Each attachment shows the filename twice (display + URL), so 3 attachments = 6 occurrences
            total_text_occurrences = attachments_html.count("test_file_text.txt")
            assert total_text_occurrences == 6, f"Global attachments should have 6 total occurrences of test_file_text.txt (3 attachments × 2 occurrences each), found {total_text_occurrences}"

            total_pdf_occurrences = attachments_html.count("test_file_pdf.pdf")
            assert total_pdf_occurrences == 2, f"Global attachments should have 2 occurrences of test_file_pdf.pdf (1 attachment × 2 occurrences each), found {total_pdf_occurrences}"

            # 3. Verify all attachment IDs are present in global index
            assert "att_a60d13cc-e6ca-4783-ac7c-5539e4f68584" in attachments_html, "First attachment ID not found in global index"
            assert "att_2f8e58ac-54a8-4584-a93e-25d4b27d65b1" in attachments_html, "Second attachment ID not found in global index"
            assert "att_16edd701-8b7c-4276-b1d8-975cb32cabd5" in attachments_html, "Third attachment ID not found in global index"
            assert "att_9ec66e19-458f-4fe6-8b72-6b9e112b05bf" in attachments_html, "Fourth attachment ID not found in global index"


class TestDSRReportBuilderRedactionHandling:

    def test_redaction_handling(self, privacy_request: PrivacyRequest):
        pass
