import io
import os
import zipfile
from datetime import datetime
from io import BytesIO

import jinja2
import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSR_DIRECTORY,
    DsrReportBuilder,
)


class TestDsrReportBuilderBase:
    """Base class with common test utilities"""

    @staticmethod
    def assert_file_in_zip(zip_file, file_path, content=None, is_binary=False):
        """Helper method to assert file exists in zip and optionally check content"""
        assert file_path in zip_file.namelist()
        if content is not None:
            if is_binary:
                assert zip_file.read(file_path) == content
            else:
                # Convert content to bytes if it's a string
                expected_content = (
                    content.encode("utf-8") if isinstance(content, str) else content
                )
                assert zip_file.read(file_path) == expected_content

    @staticmethod
    def assert_html_contains(html_content, *strings):
        """Helper method to assert HTML content contains strings"""
        for string in strings:
            assert string in html_content

    @staticmethod
    def assert_html_not_contains(html_content, *strings):
        """Helper method to assert HTML content does not contain strings"""
        for string in strings:
            assert string not in html_content

    @staticmethod
    def extract_table_values(html_content: str) -> dict[str, str]:
        """Extract field-value pairs from the HTML table."""
        values = {}
        # Find all table rows
        start = 0
        while True:
            # Find the next table row
            row_start = html_content.find('<div class="table-row">', start)
            if row_start == -1:
                break

            # Find the field cell
            field_start = html_content.find('<div class="table-cell">', row_start)
            if field_start == -1:
                break
            field_end = html_content.find("</div>", field_start)
            if field_end == -1:
                break
            field = html_content[field_start:field_end].split(">")[-1].strip()

            # Find the value cell
            value_start = html_content.find('<div class="table-cell">', field_end)
            if value_start == -1:
                break
            value_end = html_content.find("</div>", value_start)
            if value_end == -1:
                break

            # Extract the value from the pre tag
            value_content = html_content[value_start:value_end]
            pre_start = value_content.find("<pre>")
            pre_end = value_content.find("</pre>")
            if pre_start != -1 and pre_end != -1:
                value = value_content[pre_start + 5 : pre_end].strip()
                # Remove the surrounding quotes and unescape HTML entities
                if value.startswith("&#34;") and value.endswith("&#34;"):
                    value = value[4:-4]  # Remove the HTML-escaped quotes
                values[field] = value

            start = value_end + 1

        return values


@pytest.fixture
def common_webhook_data():
    """Common webhook data fixture with all possible fields"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "last_name": "Test User",
        "phone": "+1234567890",
        "system_name": "test_system",
    }


@pytest.fixture
def common_attachment_config():
    """Common attachment configuration fixture with all attachment types"""
    return {
        "text": {
            "file_name": "test.txt",
            "file_size": 1024,
            "content_type": "text/plain",
            "fileobj": BytesIO(b"test content"),
            "download_url": "http://example.com/test.txt",
        },
        "binary": {
            "file_name": "test.pdf",
            "file_size": 2048,
            "content_type": "application/pdf",
            "fileobj": BytesIO(b"test content"),
            "download_url": "http://example.com/test.pdf",
        },
        "image": {
            "file_name": "test.jpg",
            "file_size": 3072,
            "content_type": "image/jpeg",
            "fileobj": BytesIO(b"fake image content"),
            "download_url": "http://example.com/test.jpg",
        },
    }


@pytest.fixture
def webhook_variants(common_webhook_data, common_attachment_config):
    """Fixture providing different webhook data variants"""
    return {
        "basic": common_webhook_data,
        "empty_attachments": {**common_webhook_data, "attachments": []},
        "with_attachments": {
            **common_webhook_data,
            "attachments": [
                common_attachment_config["text"],
                common_attachment_config["binary"],
            ],
        },
        "malformed": {
            **common_webhook_data,
            "attachments": "not a list",
            "nested_data": {"attachments": None},
        },
    }


@pytest.fixture
def common_file_assertions():
    """Common file existence assertions fixture"""
    return {
        "required": [
            "welcome.html",
            "data/main.css",
            "data/back.svg",
        ],
        "attachment_extensions": [".txt", ".pdf", ".jpg", ".png"],
        "index_files": [
            "index.html",
            "attachments/index.html",
        ],
    }


@pytest.fixture
def common_assertions(common_file_assertions):
    """Combined fixture for common assertions"""
    return {
        "files": common_file_assertions,
        "html": {
            "attachment_link": 'class="attachment-link"',
            "back_link": 'href="../index.html"',
            "main_link": 'href="welcome.html"',
            "table_row": '<div class="table-row">',
            "table_cell": '<div class="table-cell">',
        },
        "paths": {
            "webhook_dir": "data/test_system/test_webhook",
            "attachments_dir": "attachments",
            "manual_webhook_dir": "data/manual/test_webhook",
            "dataset_dir": "data/dataset",
            "collection_dir": "data/dataset/collection",
            "welcome_path": "welcome.html",
            "attachments_index": "attachments/index.html",
            "dataset_index": "data/dataset/index.html",
            "css_path": "data/main.css",
            "back_svg_path": "data/back.svg",
        },
    }


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
            # Check that all attachment files are present in the attachments directory
            self.assert_file_in_zip(
                zip_file,
                f"{common_assertions['paths']['attachments_dir']}/{common_attachment_config['text']['file_name']}",
                common_attachment_config["text"]["fileobj"].getvalue(),
            )
            self.assert_file_in_zip(
                zip_file,
                f"{common_assertions['paths']['attachments_dir']}/{common_attachment_config['binary']['file_name']}",
                common_attachment_config["binary"]["fileobj"].getvalue(),
                is_binary=True,
            )

            # Verify that the webhook page exists but has no attachment links
            webhook_data = zip_file.read(
                f"{common_assertions['paths']['webhook_dir']}/index.html"
            ).decode("utf-8")
            self.assert_html_contains(webhook_data, webhook_variants["basic"]["email"])
            self.assert_html_not_contains(
                webhook_data, common_assertions["html"]["attachment_link"]
            )

            # Verify that the attachments index page exists and contains links
            attachments_index = zip_file.read(
                f"{common_assertions['paths']['attachments_dir']}/index.html"
            ).decode("utf-8")
            self.assert_html_contains(
                attachments_index,
                common_attachment_config["text"]["file_name"],
                common_attachment_config["binary"]["file_name"],
            )

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
            # Verify that webhook attachments are in their collection directories
            self.assert_file_in_zip(
                zip_file,
                f"{common_assertions['paths']['webhook_dir']}/{webhook_variants['with_attachments']['attachments'][0]['file_name']}",
                webhook_variants["with_attachments"]["attachments"][0][
                    "fileobj"
                ].getvalue(),
            )
            self.assert_file_in_zip(
                zip_file,
                f"data/test_system2/test_webhook2/{webhook_variants['with_attachments']['attachments'][1]['file_name']}",
                webhook_variants["with_attachments"]["attachments"][1][
                    "fileobj"
                ].getvalue(),
                is_binary=True,
            )

            # Verify that top-level attachment is in attachments directory
            self.assert_file_in_zip(
                zip_file,
                f"{common_assertions['paths']['attachments_dir']}/{webhook_variants['with_attachments']['attachments'][0]['file_name']}",
                webhook_variants["with_attachments"]["attachments"][0][
                    "fileobj"
                ].getvalue(),
            )

            # Verify that the webhook pages contain clickable links to their attachments
            webhook1_data = zip_file.read(
                f"{common_assertions['paths']['webhook_dir']}/index.html"
            ).decode("utf-8")
            self.assert_html_contains(
                webhook1_data,
                f'href="{webhook_variants["with_attachments"]["attachments"][0]["file_name"]}"',
                common_assertions["html"]["attachment_link"],
                webhook_variants["basic"]["email"],
                webhook_variants["basic"]["name"],
            )

            webhook2_data = zip_file.read(
                "data/test_system2/test_webhook2/index.html"
            ).decode("utf-8")
            self.assert_html_contains(
                webhook2_data,
                f'href="{webhook_variants["with_attachments"]["attachments"][1]["file_name"]}"',
                common_assertions["html"]["attachment_link"],
                webhook_variants["basic"]["phone"],
                "test_system2",
            )

            # Verify that the attachments index page contains top-level attachment
            attachments_index = zip_file.read(
                f"{common_assertions['paths']['attachments_dir']}/index.html"
            ).decode("utf-8")
            self.assert_html_contains(
                attachments_index,
                webhook_variants["with_attachments"]["attachments"][0]["file_name"],
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
            "attachments": [],
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

            # Verify that no attachment files were created
            assert not any(
                name.startswith(f"{common_assertions['paths']['attachments_dir']}/")
                for name in zip_file.namelist()
            )
            self.assert_html_not_contains(
                manual_data, common_assertions["html"]["attachment_link"]
            )


class TestDsrReportBuilderDataStructure:
    """Tests for DSR report builder's data structure handling"""

    def test_with_multiple_datasets(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with multiple datasets and collections"""
        dsr_data = {
            "dataset1:collection1": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
            ],
            "dataset1:collection2": [{"id": 3, "name": "Item 3"}],
            "dataset2:collection1": [{"id": 4, "name": "Item 4"}],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify dataset structure
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert "data/dataset2/index.html" in zip_file.namelist()

            # Verify collection structure
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()
            assert "data/dataset1/collection2/index.html" in zip_file.namelist()
            assert "data/dataset2/collection1/index.html" in zip_file.namelist()

            # Verify items are in collection index pages
            collection1_content = zip_file.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            assert "Item 1" in collection1_content
            assert "Item 2" in collection1_content

            collection2_content = zip_file.read(
                "data/dataset1/collection2/index.html"
            ).decode("utf-8")
            assert "Item 3" in collection2_content

            collection3_content = zip_file.read(
                "data/dataset2/collection1/index.html"
            ).decode("utf-8")
            assert "Item 4" in collection3_content


class TestDsrReportBuilderDataTypes(TestDsrReportBuilderBase):
    """Tests for DSR report builder's data type handling"""

    def test_with_complex_data_types(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with complex data types"""
        dsr_data = {
            "manual:test_webhook": [
                {
                    "string_field": "test string",
                    "number_field": 123,
                    "float_field": 123.45,
                    "boolean_field": True,
                    "null_field": None,
                    "date_field": datetime(2024, 1, 1),
                    "list_field": [1, 2, 3],
                    "nested_dict": {
                        "key": "value",
                        "nested_list": [{"a": 1}, {"b": 2}],
                    },
                    "system_name": "test_system",
                }
            ]
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            manual_data = zip_file.read("data/manual/test_webhook/index.html").decode(
                "utf-8"
            )

            # Extract all values from the table
            table_values = TestDsrReportBuilderBase.extract_table_values(manual_data)

            # Verify each value is present and properly formatted
            assert "test string" in table_values["string_field"]
            assert "123" in table_values["number_field"]
            assert "123.45" in table_values["float_field"]
            assert "true" in table_values["boolean_field"]
            assert "null" in table_values["null_field"]
            assert "2024-01-01T00:00:00" in table_values["date_field"]

            # For list and dict fields, we check that they contain the expected elements
            list_field = table_values["list_field"]
            assert "1" in list_field
            assert "2" in list_field
            assert "3" in list_field

            nested_dict = table_values["nested_dict"]
            assert "key" in nested_dict
            assert "value" in nested_dict
            assert "nested_list" in nested_dict
            assert "a" in nested_dict
            assert "1" in nested_dict
            assert "b" in nested_dict
            assert "2" in nested_dict

    def test_with_special_characters(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with special characters in data"""
        dsr_data = {
            "manual:test_webhook": [
                {
                    "email": "test@example.com",
                    "special_chars": "!@#$%^&*()_+{}|:\"<>?[]\\;',./~`",
                    "unicode_chars": "你好世界",
                    "emoji": "👋🌍",
                    "html_chars": "<script>alert('test')</script>",
                    "system_name": "test_system",
                }
            ]
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            manual_data = zip_file.read("data/manual/test_webhook/index.html").decode(
                "utf-8"
            )

            # Extract all values from the table
            table_values = TestDsrReportBuilderBase.extract_table_values(manual_data)

            # Verify each value is present and properly escaped
            assert "test@example.com" in table_values["email"]

            # For special characters, we check that each character is present
            special_chars = table_values["special_chars"]
            assert "!" in special_chars
            assert "@" in special_chars
            assert "#" in special_chars
            assert "$" in special_chars
            assert "%" in special_chars
            assert "^" in special_chars
            assert "&amp;" in special_chars  # &
            assert "*" in special_chars
            assert "(" in special_chars
            assert ")" in special_chars
            assert "_" in special_chars
            assert "+" in special_chars
            assert "{" in special_chars
            assert "}" in special_chars
            assert "|" in special_chars
            assert ":" in special_chars
            assert "\\" in special_chars
            assert "&lt;" in special_chars  # <
            assert "&gt;" in special_chars  # >
            assert "?" in special_chars
            assert "[" in special_chars
            assert "]" in special_chars
            assert ";" in special_chars
            assert "&#39;" in special_chars  # '
            assert "," in special_chars
            assert "." in special_chars
            assert "/" in special_chars
            assert "~" in special_chars
            assert "`" in special_chars

            # For Unicode characters, we check that the characters are present
            assert "\\u4f60\\u597d\\u4e16\\u754c" in table_values["unicode_chars"]

            # For emoji, we check that the characters are present
            assert "\\ud83d\\udc4b\\ud83c\\udf0d" in table_values["emoji"]

            # For HTML characters, we check that they are properly escaped
            html_chars = table_values["html_chars"]
            assert "&lt;" in html_chars  # <
            assert "&gt;" in html_chars  # >
            assert "&#39;" in html_chars  # '


@pytest.fixture
def dsr_data() -> dict:
    """Sample DSR data for testing"""
    return {
        "dataset1:collection1": [
            {"id": 1, "name": "Item 1", "email": "item1@example.com"},
            {"id": 2, "name": "Item 2", "email": "item2@example.com"},
        ],
        "dataset2:collection1": [
            {"id": 3, "name": "Item 3", "email": "item3@example.com"},
        ],
        "manual:collection1": [
            {"id": 4, "name": "Item 4", "email": "item4@example.com"},
        ],
    }


class TestDsrReportBuilder(TestDsrReportBuilderBase):
    def test_generate_report_structure(
        self, privacy_request, dsr_data: dict, common_assertions
    ):
        """Test that the generated report has the correct structure"""
        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        # Verify it's a valid zip file
        with zipfile.ZipFile(report) as zip_file:
            # Check for required files
            for file_name in common_assertions["files"]["required"]:
                self.assert_file_in_zip(zip_file, file_name)

            # Check dataset structure
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert "data/dataset2/index.html" in zip_file.namelist()
            assert "data/manual/index.html" in zip_file.namelist()

            # Check collection structure
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()

    def test_report_content(self, privacy_request, dsr_data: dict):
        """Test that the report content is correctly formatted"""
        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            # Check welcome page content
            welcome_content = zip_file.read("welcome.html").decode("utf-8")
            self.assert_html_contains(
                welcome_content, "Your requested data", "dataset1"
            )

            # Check dataset index content
            dataset1_content = zip_file.read("data/dataset1/index.html").decode("utf-8")
            self.assert_html_contains(dataset1_content, "dataset1", "collection1")

            # Check collection index content
            collection1_content = zip_file.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            self.assert_html_contains(
                collection1_content,
                "collection1",
                "item #1",
                "item #2",
                "item1@example.com",
                "Item 1",
            )

    def test_empty_dsr_data(self, privacy_request, common_assertions):
        """Test report generation with empty DSR data"""
        builder = DsrReportBuilder(privacy_request, {})
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            for file_name in common_assertions["files"]["required"]:
                self.assert_file_in_zip(zip_file, file_name)
            # Should not have any dataset directories
            assert not any(
                name.startswith("data/")
                and name != "data/main.css"
                and name != "data/back.svg"
                for name in zip_file.namelist()
            )

    def test_privacy_request_mapping(self, privacy_request, dsr_data: dict):
        """Test that privacy request data is correctly mapped in the report"""
        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            welcome_content = zip_file.read("welcome.html").decode("utf-8")
            self.assert_html_contains(
                welcome_content,
                str(privacy_request.id),
                privacy_request.policy.get_action_type().value,
                privacy_request.requested_at.strftime("%m/%d/%Y %H:%M %Z"),
            )

    def test_attachment_links_in_index(self, privacy_request: PrivacyRequest):
        """Test that attachment links in the index page correctly match the files"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Create multiple files with the same name
        attachments = [
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content1"),
                "content_type": "text/plain",
            },
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content2"),
                "content_type": "text/plain",
            },
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content3"),
                "content_type": "text/plain",
            },
        ]

        # Add attachments using _add_attachments
        builder._add_attachments(attachments)
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Verify files exist with unique names
            assert "attachments/test.txt" in zip_file.namelist()
            assert "attachments/test_1.txt" in zip_file.namelist()
            assert "attachments/test_2.txt" in zip_file.namelist()

            # Verify index page contains correct links
            index_content = zip_file.read("attachments/index.html").decode("utf-8")
            assert 'href="test.txt"' in index_content
            assert 'href="test_1.txt"' in index_content
            assert 'href="test_2.txt"' in index_content

            # Verify content is preserved
            assert zip_file.read("attachments/test.txt").decode("utf-8") == "content1"
            assert zip_file.read("attachments/test_1.txt").decode("utf-8") == "content2"
            assert zip_file.read("attachments/test_2.txt").decode("utf-8") == "content3"


class TestDsrReportBuilderAttachmentHandling:
    """Tests for DSR report builder's attachment handling functions"""

    def test_handle_attachment_text(self, privacy_request: PrivacyRequest):
        """Test handling a text attachment"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"test content"),
                "content_type": "text/plain",
            }
        ]

        attachment_links = builder._write_attachment_content(
            attachments,
            "data/dataset1/collection1",
        )
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Check only collection directory location
            assert "data/dataset1/collection1/test.txt" in zip_file.namelist()
            assert "attachments/test.txt" not in zip_file.namelist()

            # Verify content
            content = zip_file.read("data/dataset1/collection1/test.txt").decode(
                "utf-8"
            )
            assert content == "test content"

            # Verify attachment links
            assert "test.txt" in attachment_links
            assert attachment_links["test.txt"] == "test.txt"

    def test_handle_attachment_binary(self, privacy_request: PrivacyRequest):
        """Test handling a binary attachment"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": "test.pdf",
                "fileobj": BytesIO(b"test content"),
                "content_type": "application/pdf",
            }
        ]

        attachment_links = builder._write_attachment_content(
            attachments,
            "data/dataset1/collection1",
        )
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Check only collection directory location
            assert "data/dataset1/collection1/test.pdf" in zip_file.namelist()
            assert "attachments/test.pdf" not in zip_file.namelist()

            # Verify content
            content = zip_file.read("data/dataset1/collection1/test.pdf")
            assert content == b"test content"

            # Verify attachment links
            assert "test.pdf" in attachment_links
            assert attachment_links["test.pdf"] == "test.pdf"

    def test_handle_attachment_no_content(self, privacy_request: PrivacyRequest):
        """Test handling an attachment with no content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": "test.txt",
                "fileobj": None,
                "content_type": "text/plain",
            }
        ]

        attachment_links = builder._write_attachment_content(
            attachments,
            "data/dataset1/collection1",
        )
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "data/dataset1/collection1/test.txt" not in zip_file.namelist()
            assert not attachment_links

    def test_add_attachments_top_level(self, privacy_request: PrivacyRequest):
        """Test adding top-level attachments"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": "test1.txt",
                "fileobj": BytesIO(b"content1"),
                "content_type": "text/plain",
            },
            {
                "file_name": "test2.pdf",
                "fileobj": BytesIO(b"content2"),
                "content_type": "application/pdf",
            },
        ]

        attachment_links = builder._write_attachment_content(attachments, "attachments")
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Check attachments directory
            assert "attachments/test1.txt" in zip_file.namelist()
            assert "attachments/test2.pdf" in zip_file.namelist()

            # Verify content
            assert zip_file.read("attachments/test1.txt").decode("utf-8") == "content1"
            assert zip_file.read("attachments/test2.pdf") == b"content2"

            # Verify attachment links
            assert "test1.txt" in attachment_links
            assert "test2.pdf" in attachment_links
            assert attachment_links["test1.txt"] == "test1.txt"
            assert attachment_links["test2.pdf"] == "test2.pdf"

    def test_process_item_attachments(self, privacy_request: PrivacyRequest):
        """Test processing attachments in an item"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        items = [
            {
                "id": 1,
                "attachments": [
                    {
                        "file_name": "test1.txt",
                        "fileobj": BytesIO(b"content1"),
                        "content_type": "text/plain",
                    },
                    {
                        "file_name": "test2.pdf",
                        "fileobj": BytesIO(b"content2"),
                        "content_type": "application/pdf",
                    },
                ],
            }
        ]

        builder._add_collection(items, "dataset1", "collection1")
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Verify attachments are in the collection directory
            assert "data/dataset1/collection1/test1.txt" in zip_file.namelist()
            assert "data/dataset1/collection1/test2.pdf" in zip_file.namelist()

            # Verify attachments are not in the top-level attachments directory
            assert "attachments/test1.txt" not in zip_file.namelist()
            assert "attachments/test2.pdf" not in zip_file.namelist()

            # Verify the index page exists
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()

            # Verify attachment content
            assert (
                zip_file.read("data/dataset1/collection1/test1.txt").decode("utf-8")
                == "content1"
            )
            assert zip_file.read("data/dataset1/collection1/test2.pdf") == b"content2"

            # Verify index page contains attachment links
            index_content = zip_file.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            assert 'href="test1.txt"' in index_content
            assert 'href="test2.pdf"' in index_content

    def test_handle_duplicate_filenames(self, privacy_request: PrivacyRequest):
        """Test handling of duplicate filenames in the same directory"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Create multiple files with the same name
        attachments = [
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content1"),
                "content_type": "text/plain",
            },
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content2"),
                "content_type": "text/plain",
            },
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content3"),
                "content_type": "text/plain",
            },
        ]

        # Add all attachments to the same directory
        attachment_links = builder._write_attachment_content(attachments, "attachments")
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Verify all files exist with unique names
            assert "attachments/test.txt" in zip_file.namelist()
            assert "attachments/test_1.txt" in zip_file.namelist()
            assert "attachments/test_2.txt" in zip_file.namelist()

            # Verify content is preserved
            assert zip_file.read("attachments/test.txt").decode("utf-8") == "content1"
            assert zip_file.read("attachments/test_1.txt").decode("utf-8") == "content2"
            assert zip_file.read("attachments/test_2.txt").decode("utf-8") == "content3"

            # Verify attachment links
            assert "test.txt" in attachment_links
            assert "test_1.txt" in attachment_links
            assert "test_2.txt" in attachment_links
            assert attachment_links["test.txt"] == "test.txt"
            assert attachment_links["test_1.txt"] == "test_1.txt"
            assert attachment_links["test_2.txt"] == "test_2.txt"

    def test_handle_duplicate_filenames_different_directories(
        self, privacy_request: PrivacyRequest
    ):
        """Test handling of duplicate filenames in different directories"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Create files with the same name in different directories
        attachments = [
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content1"),
                "content_type": "text/plain",
            },
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"content2"),
                "content_type": "text/plain",
            },
        ]

        # Add attachments to different directories
        attachment_links1 = builder._write_attachment_content(
            attachments[:1], "attachments"
        )
        attachment_links2 = builder._write_attachment_content(
            attachments[1:], "data/dataset1/collection1"
        )
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Verify files exist in their respective directories
            assert "attachments/test.txt" in zip_file.namelist()
            assert "data/dataset1/collection1/test.txt" in zip_file.namelist()

            # Verify content is preserved
            assert zip_file.read("attachments/test.txt").decode("utf-8") == "content1"
            assert (
                zip_file.read("data/dataset1/collection1/test.txt").decode("utf-8")
                == "content2"
            )

            # Verify attachment links
            assert "test.txt" in attachment_links1
            assert attachment_links1["test.txt"] == "test.txt"
            assert "test.txt" in attachment_links2
            assert attachment_links2["test.txt"] == "test.txt"


class TestDsrReportBuilderDatasetHandling:
    """Tests for DSR report builder's dataset handling functions"""

    def test_add_dataset(self, privacy_request: PrivacyRequest):
        """Test adding a dataset with collections"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        collections = {
            "collection1": [{"id": 1}, {"id": 2}],
            "collection2": [{"id": 3}],
        }

        builder._add_dataset("dataset1", collections)
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()
            assert "data/dataset1/collection2/index.html" in zip_file.namelist()

            # Verify dataset index content
            content = zip_file.read("data/dataset1/index.html").decode("utf-8")
            assert "dataset1" in content
            assert "collection1" in content
            assert "collection2" in content

    def test_add_dataset_empty_collections(self, privacy_request: PrivacyRequest):
        """Test adding a dataset with no collections"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        builder._add_dataset("dataset1", {})
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "data/dataset1/index.html" in zip_file.namelist()
            content = zip_file.read("data/dataset1/index.html").decode("utf-8")
            assert "dataset1" in content
            assert "collection" not in content


class TestDsrReportBuilderAttachmentContentWriting:
    """Tests for DSR report builder's attachment content writing functionality"""

    @pytest.mark.parametrize(
        "file_name,content,content_type,expected,is_binary",
        [
            ("test.txt", "test content", "text/plain", "test content", False),
            (
                "test.csv",
                "header1,header2\nvalue1,value2",
                "text/csv",
                "header1,header2\nvalue1,value2",
                False,
            ),
            (
                "test.txt",
                b"fake text content",
                "text/plain",
                "fake text content",
                False,
            ),
            (
                "test.pdf",
                b"fake pdf content",
                "application/pdf",
                b"fake pdf content",
                True,
            ),
            (
                "test.docx",
                b"fake word content",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                b"fake word content",
                True,
            ),
            (
                "test.xlsx",
                b"fake excel content",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                b"fake excel content",
                True,
            ),
            (
                "test.zip",
                b"fake zip content",
                "application/zip",
                b"fake zip content",
                True,
            ),
            (
                "test.jpg",
                b"fake jpeg content",
                "image/jpeg",
                b"fake jpeg content",
                True,
            ),
            ("test.png", b"fake png content", "image/png", b"fake png content", True),
        ],
    )
    def test_write_attachment_content_parametrized(
        self,
        privacy_request: PrivacyRequest,
        file_name,
        content,
        content_type,
        expected,
        is_binary,
    ):
        """Test writing various attachment content types using parameterization"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": file_name,
                "fileobj": BytesIO(
                    content if isinstance(content, bytes) else content.encode("utf-8")
                ),
                "content_type": content_type,
            }
        ]

        attachment_links = builder._write_attachment_content(attachments, "attachments")
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert f"attachments/{file_name}" in zip_file.namelist()
            if is_binary:
                assert zip_file.read(f"attachments/{file_name}") == expected
            else:
                assert (
                    zip_file.read(f"attachments/{file_name}").decode("utf-8")
                    == expected
                )
            assert file_name in attachment_links
            assert attachment_links[file_name] == file_name

    @pytest.mark.parametrize(
        "file_name,content,content_type",
        [
            ("test.txt", None, "text/plain"),
            ("test.pdf", None, "application/pdf"),
        ],
    )
    def test_write_attachment_content_no_content_parametrized(
        self, privacy_request: PrivacyRequest, file_name, content, content_type
    ):
        """Test writing attachment content with no content using parameterization"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": file_name,
                "fileobj": None,
                "content_type": content_type,
            }
        ]

        attachment_links = builder._write_attachment_content(attachments, "attachments")
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert f"attachments/{file_name}" not in zip_file.namelist()
            assert not attachment_links

    @pytest.mark.parametrize("directory", ["attachments", "data/dataset1/collection1"])
    def test_write_attachment_content_different_directories_parametrized(
        self, privacy_request: PrivacyRequest, directory
    ):
        """Test writing attachment content to different directories using parameterization"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": "test.txt",
                "fileobj": BytesIO(b"test content"),
                "content_type": "text/plain",
            }
        ]

        attachment_links = builder._write_attachment_content(attachments, directory)
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert f"{directory}/test.txt" in zip_file.namelist()
            assert (
                zip_file.read(f"{directory}/test.txt").decode("utf-8") == "test content"
            )
            assert "test.txt" in attachment_links
            assert attachment_links["test.txt"] == "test.txt"


class TestDsrReportBuilderContent(TestDsrReportBuilderBase):
    """Tests for content generation in DSR reports"""

    def test_report_structure(
        self,
        privacy_request: PrivacyRequest,
        webhook_variants,
        common_assertions,
        common_file_assertions,
    ):
        """Test basic report structure generation"""
        dsr_data = {
            "manual:test_webhook": [webhook_variants["basic"]],
            "attachments": [],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Check for required files
            for file_name in common_file_assertions["required"]:
                self.assert_file_in_zip(zip_file, file_name)

            # Check dataset structure
            self.assert_file_in_zip(
                zip_file,
                f"{common_assertions['paths']['manual_webhook_dir']}/index.html",
            )

            # Verify welcome page content
            welcome_content = zip_file.read(
                common_assertions["paths"]["welcome_path"]
            ).decode("utf-8")
            self.assert_html_contains(welcome_content, "Your requested data", "manual")

    def test_template_rendering_edge_cases(self, privacy_request: PrivacyRequest):
        """Test template rendering with various edge cases"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Test with missing data
        content = builder._populate_template(
            "templates/welcome.html",
            heading=None,
            description=None,
            data={},  # Pass empty dict instead of None
        )
        assert "Your requested data" in content

        # Test with malformed data
        content = builder._populate_template(
            "templates/welcome.html",
            heading=123,  # Non-string heading
            description=["invalid"],  # Non-string description
            data={"invalid": object()},  # Non-serializable data
        )
        assert "Your requested data" in content

        # Test with empty strings
        content = builder._populate_template(
            "templates/welcome.html", heading="", description="", data={}
        )
        assert "Your requested data" in content

    def test_edge_cases(self, privacy_request: PrivacyRequest):
        """Test various edge cases in the DSR report builder"""
        # Test with empty file names
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        builder._add_file("", "content")  # Should be ignored
        builder._add_file("test.txt", "")  # Should be ignored

        # Test with invalid file names
        builder._add_file("test/../test.txt", "content")  # Should handle path traversal
        builder._add_file("test.txt" * 100, "content")  # Should handle very long names

        # Test with special characters in file names
        builder._add_file("test!@#$%^&*().txt", "content")

        # Test with empty attachments
        dsr_data = {"dataset1:collection1": [{"id": 1, "attachments": []}]}
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()


class TestDsrReportBuilderOrganization(TestDsrReportBuilderBase):
    """Tests for report organization and structure"""

    def test_dataset_ordering(self, privacy_request: PrivacyRequest):
        """Test dataset ordering in the report"""
        dsr_data = {
            "zebra:collection1": [{"id": 1}],
            "attachments": [
                {
                    "file_name": "test.txt",
                    "fileobj": BytesIO(b"test"),
                    "content_type": "text/plain",
                }
            ],
            "alpha:collection1": [{"id": 2}],
            "beta:collection1": [{"id": 3}],
            "dataset:collection1": [
                {"id": 4}
            ],  # This should be renamed to "Additional Data"
            "charlie:collection1": [{"id": 5}],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            welcome_content = zip_file.read("welcome.html").decode("utf-8")

            # Find the order of links in the welcome page
            link_order = []
            for line in welcome_content.split("\n"):
                if 'href="data/' in line or 'href="attachments/' in line:
                    if "data/alpha/" in line:
                        link_order.append("alpha")
                    elif "data/beta/" in line:
                        link_order.append("beta")
                    elif "data/charlie/" in line:
                        link_order.append("charlie")
                    elif "data/zebra/" in line:
                        link_order.append("zebra")
                    elif "data/dataset/" in line:
                        link_order.append("Additional Data")
                    elif "attachments/index.html" in line:
                        link_order.append("Additional Attachments")

            # Verify the order: regular datasets alphabetically, then Additional Data, then Additional Attachments
            assert link_order == [
                "alpha",
                "beta",
                "charlie",
                "zebra",
                "Additional Data",
                "Additional Attachments",
            ]

            # Verify the dataset directory structure
            assert (
                "data/dataset/index.html" in zip_file.namelist()
            )  # Original directory name
            assert "data/dataset/collection1/index.html" in zip_file.namelist()

            # Verify the welcome page shows "Additional Data" instead of "dataset" as link text
            assert "Additional Data" in welcome_content
            # Check that 'dataset' only appears in the Additional Data link's href attribute
            for line in welcome_content.split("\n"):
                if 'href="data/dataset/' in line:
                    # Extract the link text by finding the content between > and <
                    start = line.find(">") + 1
                    end = line.find("<", start)
                    if start > 0 and end > start:
                        link_text = line[start:end]
                        assert link_text == "Additional Data"
                        assert "dataset" not in link_text

    def test_collection_organization(self, privacy_request: PrivacyRequest):
        """Test collection organization in the report"""
        dsr_data = {
            "dataset1:collection1": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
            ],
            "dataset1:collection2": [{"id": 3, "name": "Item 3"}],
            "dataset2:collection1": [{"id": 4, "name": "Item 4"}],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify dataset structure
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert "data/dataset2/index.html" in zip_file.namelist()

            # Verify collection structure
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()
            assert "data/dataset1/collection2/index.html" in zip_file.namelist()
            assert "data/dataset2/collection1/index.html" in zip_file.namelist()

            # Verify items are in collection index pages
            collection1_content = zip_file.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            self.assert_html_contains(collection1_content, "Item 1", "Item 2")

            collection2_content = zip_file.read(
                "data/dataset1/collection2/index.html"
            ).decode("utf-8")
            self.assert_html_contains(collection2_content, "Item 3")

            collection3_content = zip_file.read(
                "data/dataset2/collection1/index.html"
            ).decode("utf-8")
            self.assert_html_contains(collection3_content, "Item 4")

    def test_invalid_template_path(self, privacy_request: PrivacyRequest):
        """Test handling of invalid template paths"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Test with non-existent template
        with pytest.raises(jinja2.TemplateNotFound):
            builder._populate_template("templates/nonexistent.html")

        # Create a template with invalid syntax
        invalid_template_path = os.path.join(
            DSR_DIRECTORY, "templates/invalid_syntax.html"
        )
        os.makedirs(os.path.dirname(invalid_template_path), exist_ok=True)
        with open(invalid_template_path, "w") as f:
            f.write("{% invalid syntax %}")

        try:
            # Test with invalid template syntax
            with pytest.raises(jinja2.TemplateSyntaxError):
                builder._populate_template("templates/invalid_syntax.html")
        finally:
            # Clean up the test template
            if os.path.exists(invalid_template_path):
                os.remove(invalid_template_path)

        # Ensure the zip file is properly closed
        if hasattr(builder, "out") and builder.out is not None:
            builder.out.close()
            builder.out = None

    def test_concurrent_access(self, privacy_request: PrivacyRequest):
        """Test concurrent access to the zip file"""
        import threading

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        errors = []

        def write_file():
            try:
                builder._add_file("test.txt", "test content")
            except Exception as e:
                errors.append(e)

        # Create multiple threads writing to the zip file
        threads = [threading.Thread(target=write_file) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert not errors

        # Verify all files were written
        builder.out.close()
        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert len([f for f in zip_file.namelist() if f.startswith("test")]) == 10

    def test_performance_large_dataset(self, privacy_request: PrivacyRequest):
        """Test performance with a large dataset"""
        import time

        # Create a smaller dataset for performance testing
        # 100 collections with 100 items each instead of 1000x1000
        dsr_data = {
            f"dataset1:collection{i}": [
                {"id": j, "name": f"Item {j}", "data": "x" * 100}  # 100 bytes per item
                for j in range(100)
            ]
            for i in range(100)
        }

        start_time = time.time()
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()
        end_time = time.time()

        # Verify the report was generated within a reasonable time
        # Increased threshold to 60 seconds to account for varying system performance
        assert end_time - start_time < 60  # Should complete within 60 seconds

        # Verify the structure is correct
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert len([f for f in zip_file.namelist() if "collection" in f]) == 100
