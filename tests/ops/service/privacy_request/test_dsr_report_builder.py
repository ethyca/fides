import io
import re
import threading
import time
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request_redaction_patterns import (
    PrivacyRequestRedactionPatterns,
)
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSRReportBuilder,
)


class TestDSRReportBuilderBase:
    """Base class with common test utilities"""

    @staticmethod
    def assert_file_in_zip(zip_file, file_path, content=None, is_binary=False):
        """Assert that a file exists in the zip file and optionally check its content."""
        assert file_path in zip_file.namelist()
        if content is not None:
            if is_binary:
                assert zip_file.read(file_path) == content
            else:
                assert zip_file.read(file_path).decode("utf-8") == content

    @staticmethod
    def assert_html_contains(html_content, *strings):
        """Assert that the HTML content contains all the given strings."""
        for string in strings:
            assert string in html_content

    @staticmethod
    def assert_html_not_contains(html_content, *strings):
        """Assert that the HTML content does not contain any of the given strings."""
        for string in strings:
            assert string not in html_content

    @staticmethod
    def extract_table_values(html_content: str) -> dict[str, str]:
        """Extract values from HTML table cells."""
        values = {}
        # Find all table rows (div with class table-row), being lenient with whitespace
        rows = re.findall(
            r'<div\s+class="table-row">\s*<div\s+class="table-cell">(.*?)</div>\s*<div\s+class="table-cell">(.*?)</div>\s*</div>',
            html_content,
            re.DOTALL,
        )

        for i, (key_cell, value_cell) in enumerate(rows):
            # Extract the key
            key = re.sub(r"<[^>]+>", "", key_cell).strip()

            # Extract the value from pre tag
            value_match = re.search(r"<pre>(.*?)</pre>", value_cell, re.DOTALL)
            if value_match:
                value = value_match.group(1).strip()
                # Unescape HTML entities
                value = value.replace("&#34;", '"')
                if key and value:  # Only add non-empty values
                    values[key] = value

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
    """Common assertions for DSR report builder tests"""
    return {
        "files": common_file_assertions,
        "paths": {
            "webhook_dir": "data/test_system/test_webhook",
            "webhook_dir2": "data/test_system2/test_webhook2",
            "attachments_dir": "attachments",
            "manual_webhook_dir": "data/manual/test_webhook",
            "welcome_path": "welcome.html",
            "attachments_index": "attachments/index.html",
            "back_svg_path": "data/back.svg",
            "collection_dir": "data/dataset/collection",
            "collection_index": "data/dataset/collection/index.html",
            "item_index": "data/dataset/collection/item_index.html",
        },
        "html": {
            "attachment_link": "attachment-link",
            "attachment_size": "attachment-size",
            "attachment_name": "attachment-name",
        },
    }


class TestDsrReportBuilderAttachments(TestDSRReportBuilderBase):
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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
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
            "attachments": [],
        }

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
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

    def test_selective_redaction_with_patterns(
        self, privacy_request: PrivacyRequest, db
    ):
        """Test DSR report builder with selective redaction based on regex patterns"""

        # Set up redaction patterns that will match some but not all names
        redaction_patterns = [
            r"customer.*",  # Matches "customer_database" but not "analytics_system"
            r".*user.*",  # Matches "users" and "user_events" but not "orders"
            r"^email$",  # Matches exact field name "email" but not "name" or "id"
        ]

        # Create or update redaction patterns in database
        PrivacyRequestRedactionPatterns.create_or_update(
            db=db, data={"patterns": redaction_patterns}
        )

        dsr_data = {
            "customer_database:users": [
                {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25},
            ],
            "customer_database:orders": [
                {"id": 101, "user_id": 1, "amount": 49.99, "product": "Widget A"},
                {"id": 102, "user_id": 2, "amount": 29.99, "product": "Widget B"},
            ],
            "analytics_system:user_events": [
                {"user_id": 1, "event": "login", "timestamp": "2024-01-01T10:00:00Z"},
                {
                    "user_id": 1,
                    "event": "purchase",
                    "timestamp": "2024-01-01T10:30:00Z",
                },
            ],
            "public_data:articles": [
                {"id": 1, "title": "Public Article", "content": "This is public"},
                {"id": 2, "title": "Another Article", "content": "Also public"},
            ],
        }

        # Build DSR report - redaction patterns are automatically loaded from privacy request's session
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        # Save the DSR package to a file for inspection
        output_file = Path("/tmp/dsr_package_selective_redaction.zip")
        with open(output_file, "wb") as file:
            file.write(report.getvalue())

        # Basic verification that the package was created correctly
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify the package structure
        with zipfile.ZipFile(output_file, "r") as zip_file:
            # Check welcome page content
            welcome_content = zip_file.read("welcome.html").decode("utf-8")

            # Dataset-level redaction:
            # "analytics_system" should NOT be redacted (doesn't match "customer.*")
            # "customer_database" should be redacted to "dataset_2" (matches "customer.*", gets index 2)
            # "public_data" should NOT be redacted (no pattern match)
            assert (
                "analytics_system" in welcome_content
            )  # analytics_system NOT redacted
            assert "dataset_2" in welcome_content  # customer_database redacted
            assert "public_data" in welcome_content  # public_data NOT redacted

            # Verify dataset directory structure exists (uses redacted names for file paths)
            assert "data/dataset_2/index.html" in zip_file.namelist()
            assert "data/analytics_system/index.html" in zip_file.namelist()
            assert "data/public_data/index.html" in zip_file.namelist()

            # Check dataset index pages for collection-level redaction
            customer_dataset_content = zip_file.read(
                "data/dataset_2/index.html"
            ).decode("utf-8")
            # "users" should be redacted to "collection_1" (matches ".*user.*")
            # "orders" should NOT be redacted (no pattern match)
            assert "collection_1" in customer_dataset_content  # users redacted
            assert "orders" in customer_dataset_content  # orders NOT redacted

            analytics_dataset_content = zip_file.read(
                "data/analytics_system/index.html"
            ).decode("utf-8")
            # "user_events" should be redacted to "collection_1" (matches ".*user.*")
            assert "collection_1" in analytics_dataset_content  # user_events redacted

            public_dataset_content = zip_file.read(
                "data/public_data/index.html"
            ).decode("utf-8")
            # "articles" should NOT be redacted (no pattern match)
            assert "articles" in public_dataset_content  # articles NOT redacted

            # Check collection pages for field-level redaction
            users_collection_content = zip_file.read(
                "data/dataset_2/collection_1/index.html"
            ).decode("utf-8")
            # "email" should be redacted to "field_N" (matches "^email$")
            # "id", "name", "age" should NOT be redacted (no pattern match)
            assert "field_" in users_collection_content  # email redacted
            assert "id" in users_collection_content  # id NOT redacted
            assert "name" in users_collection_content  # name NOT redacted
            assert "age" in users_collection_content  # age NOT redacted


class TestDsrReportBuilderDataTypes(TestDSRReportBuilderBase):
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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            manual_data = zip_file.read("data/manual/test_webhook/index.html").decode(
                "utf-8"
            )

            # Extract all values from the table
            table_values = TestDSRReportBuilderBase.extract_table_values(manual_data)

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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            manual_data = zip_file.read("data/manual/test_webhook/index.html").decode(
                "utf-8"
            )

            # Extract all values from the table
            table_values = TestDSRReportBuilderBase.extract_table_values(manual_data)

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


class TestDsrReportBuilder(TestDSRReportBuilderBase):
    def test_generate_report_structure(
        self, privacy_request, dsr_data: dict, common_assertions
    ):
        """Test that the generated report has the correct structure"""
        builder = DSRReportBuilder(privacy_request, dsr_data)
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
        builder = DSRReportBuilder(privacy_request, dsr_data)
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
        builder = DSRReportBuilder(privacy_request, {})
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
        builder = DSRReportBuilder(privacy_request, dsr_data)
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
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Create multiple attachments with the same name but different URLs
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

        # Add attachments using _add_attachments
        builder._add_attachments(attachments)
        builder.out.close()

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Verify index file exists
            assert "attachments/index.html" in zip_file.namelist()

            # Read and verify the index content
            html_content = zip_file.read("attachments/index.html").decode("utf-8")

            # Check that all three files are listed with their unique names
            TestDSRReportBuilderBase.assert_html_contains(
                html_content,
                "test.txt",  # First file keeps original name
                "test_1.txt",  # Second file gets _1 suffix
                "test_2.txt",  # Third file gets _2 suffix
                "https://example.com/test1.txt",
                "https://example.com/test2.txt",
                "https://example.com/test3.txt",
                "1.0 KB",
                "2.0 KB",
                "3.0 KB",
            )


class TestDsrReportBuilderAttachmentHandling:
    """Tests for DSR report builder's attachment handling functions"""

    def test_handle_attachment_text(self, privacy_request: PrivacyRequest):
        """Test handling of text attachments with download URLs"""
        builder = DSRReportBuilder(privacy_request, {})
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
        builder = DSRReportBuilder(privacy_request, {})
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
        builder = DSRReportBuilder(privacy_request, {})
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
        builder = DSRReportBuilder(privacy_request, dsr_data)
        zip_file = builder.generate()

        # Create a ZipFile object from the BytesIO
        with zipfile.ZipFile(zip_file) as zip_file_obj:
            # Check that attachments index was created
            TestDSRReportBuilderBase.assert_file_in_zip(
                zip_file_obj, "attachments/index.html"
            )

            # Check that the HTML contains the attachment links
            html_content = zip_file_obj.read("attachments/index.html").decode("utf-8")
            TestDSRReportBuilderBase.assert_html_contains(
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

        builder = DSRReportBuilder(privacy_request, dsr_data)
        zip_file = builder.generate()

        # Create a ZipFile object from the BytesIO
        with zipfile.ZipFile(zip_file) as zip_file_obj:
            # Check that collection index was created
            TestDSRReportBuilderBase.assert_file_in_zip(
                zip_file_obj, "data/dataset1/collection1/index.html"
            )

            # Check that the HTML contains the attachment link
            html_content = zip_file_obj.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            TestDSRReportBuilderBase.assert_html_contains(
                html_content, "item1.txt", "https://example.com/item1.txt", "1.0 KB"
            )

    def test_handle_duplicate_filenames(self, privacy_request: PrivacyRequest):
        """Test handling of duplicate filenames across all directories"""
        builder = DSRReportBuilder(privacy_request, {})
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
        builder = DSRReportBuilder(privacy_request, {})

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


class TestDsrReportBuilderDatasetHandling:
    """Tests for DSR report builder's dataset handling functions"""

    def test_add_dataset(self, privacy_request: PrivacyRequest):
        """Test adding a dataset with collections"""
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data={})
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
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data={})

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
        builder = DSRReportBuilder(privacy_request, {})
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
        builder = DSRReportBuilder(privacy_request, {})
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
        builder = DSRReportBuilder(privacy_request, {})
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


class TestDsrReportBuilderContent(TestDSRReportBuilderBase):
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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
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
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data={})

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
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data={})
        builder._add_file("", "content")  # Should be ignored
        builder._add_file("test.txt", "")  # Should be ignored

        # Test with invalid file names
        builder._add_file("test/../test.txt", "content")  # Should handle path traversal
        builder._add_file("test.txt" * 100, "content")  # Should handle very long names

        # Test with special characters in file names
        builder._add_file("test!@#$%^&*().txt", "content")

        # Test with empty attachments
        dsr_data = {"dataset1:collection1": [{"id": 1, "attachments": []}]}
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()


class TestDsrReportBuilderOrganization(TestDSRReportBuilderBase):
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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
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

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
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

    def test_concurrent_access(self, privacy_request: PrivacyRequest):
        """Test concurrent access to the zip file"""

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data={})
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
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()
        end_time = time.time()

        # Verify the report was generated within a reasonable time
        # Increased threshold to 60 seconds to account for varying system performance
        assert end_time - start_time < 60  # Should complete within 60 seconds

        # Verify the structure is correct
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert len([f for f in zip_file.namelist() if "collection" in f]) == 100
