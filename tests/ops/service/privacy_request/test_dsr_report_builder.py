import io
import zipfile
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)


class TestDsrReportBuilderAttachments:
    """Tests for DSR report builder's attachment handling"""

    def test_with_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with attachments in manual webhook data"""
        # Create test data with attachments in different locations
        dsr_data = {
            "test_webhook": [
                {
                    "email": "test@example.com",
                    "system_name": "test_system",
                }
            ],
            "attachments": [
                {
                    "file_name": "test1.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                    "content": "test content 1",
                    "download_url": "http://example.com/test1.txt",
                },
                {
                    "file_name": "test2.pdf",
                    "file_size": 2048,
                    "content_type": "application/pdf",
                    "content": b"test content 2",
                    "download_url": "http://example.com/test2.pdf",
                },
                {
                    "file_name": "test3.txt",
                    "file_size": 3072,
                    "content_type": "text/plain",
                    "content": "test content 3",
                    "download_url": "http://example.com/test3.txt",
                },
            ],
        }

        # Create the DSR report
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        # Verify the report structure
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Check that all attachment files are present in the attachments directory
            # Note: Attachments are only stored in the top-level attachments directory
            # when they come from the top-level "attachments" key
            assert "attachments/test1.txt" in zip_file.namelist()
            assert "attachments/test2.pdf" in zip_file.namelist()
            assert "attachments/test3.txt" in zip_file.namelist()

            # Verify attachment content
            assert (
                zip_file.read("attachments/test1.txt").decode("utf-8")
                == "test content 1"
            )
            assert zip_file.read("attachments/test2.pdf") == b"test content 2"
            assert (
                zip_file.read("attachments/test3.txt").decode("utf-8")
                == "test content 3"
            )

            # Verify that the manual webhook page exists but has no attachment links
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )
            assert "test@example.com" in manual_data
            assert 'class="attachment-link"' not in manual_data

            # Verify that the attachments index page exists and contains links
            attachments_index = zip_file.read("attachments/index.html").decode("utf-8")
            assert "test1.txt" in attachments_index
            assert "test2.pdf" in attachments_index
            assert "test3.txt" in attachments_index

    def test_without_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with no attachments"""
        dsr_data = {
            "manual:test_webhook": [
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "attachments": [],  # Empty attachments list
                    "system_name": "test_system",
                }
            ],
            "attachments": [],  # Empty top-level attachments
        }

        # Create the DSR report
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        # Verify the report structure
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Check that no attachment files are present
            assert not any(
                name.startswith("attachments/") for name in zip_file.namelist()
            )
            assert not any(
                name.endswith(".txt") or name.endswith(".pdf")
                for name in zip_file.namelist()
            )

            # Verify manual data is present and contains no attachment links
            assert "data/manual/test_webhook/1.html" in zip_file.namelist()
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )
            assert "test@example.com" in manual_data
            assert "Test User" in manual_data
            assert 'class="attachment-link"' not in manual_data

    def test_with_empty_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with empty attachment lists"""
        dsr_data = {
            "manual:test_webhook": [
                {
                    "email": "test@example.com",
                    "attachments": [],
                    "nested_data": {"attachments": []},
                    "system_name": "test_system",
                }
            ],
            "attachments": [],
        }

        # Create the DSR report
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        # Verify the report structure
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Check that no attachment files or pages are present
            assert not any(
                name.startswith("data/attachments/") for name in zip_file.namelist()
            )

            # Verify manual data is present
            assert "data/manual/test_webhook/1.html" in zip_file.namelist()
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )
            assert "test@example.com" in manual_data

    def test_with_malformed_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with malformed attachment data"""
        dsr_data = {
            "manual:test_webhook": [
                {
                    "email": "test@example.com",
                    "attachments": "not a list",  # Malformed attachment data
                    "nested_data": {
                        "attachments": None  # Malformed nested attachment data
                    },
                    "system_name": "test_system",
                }
            ],
            "attachments": "not a list",  # Malformed top-level attachment data
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify that the report was still generated
            assert "data/manual/test_webhook/1.html" in zip_file.namelist()
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )
            assert "test@example.com" in manual_data

            # Verify that no attachment files were created
            assert not any(
                name.startswith("attachments/") for name in zip_file.namelist()
            )
            assert not any(
                name.endswith(".txt") or name.endswith(".pdf")
                for name in zip_file.namelist()
            )
            assert 'class="attachment-link"' not in manual_data

    def test_with_manual_webhook_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with attachments in manual webhook data"""
        dsr_data = {
            "manual:test_webhook": [
                {
                    "email": "test@example.com",
                    "attachments": [
                        {
                            "file_name": "webhook1.txt",
                            "file_size": 1024,
                            "content_type": "text/plain",
                            "content": "webhook content 1",
                            "download_url": "http://example.com/webhook1.txt",
                        },
                        {
                            "file_name": "webhook2.pdf",
                            "file_size": 2048,
                            "content_type": "application/pdf",
                            "content": b"webhook content 2",
                            "download_url": "http://example.com/webhook2.pdf",
                        },
                    ],
                    "system_name": "test_system",
                }
            ],
            "attachments": [
                {
                    "file_name": "top_level.txt",
                    "file_size": 3072,
                    "content_type": "text/plain",
                    "content": "top level content",
                    "download_url": "http://example.com/top_level.txt",
                }
            ],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify that webhook attachments are present in both locations
            assert "attachments/webhook1.txt" in zip_file.namelist()
            assert "attachments/webhook2.pdf" in zip_file.namelist()
            assert "data/manual/test_webhook/webhook1.txt" in zip_file.namelist()
            assert "data/manual/test_webhook/webhook2.pdf" in zip_file.namelist()

            # Verify that top-level attachment is only in attachments directory
            assert "attachments/top_level.txt" in zip_file.namelist()
            assert "data/manual/test_webhook/top_level.txt" not in zip_file.namelist()

            # Verify attachment content in both locations
            assert (
                zip_file.read("attachments/webhook1.txt").decode("utf-8")
                == "webhook content 1"
            )
            assert zip_file.read("attachments/webhook2.pdf") == b"webhook content 2"
            assert (
                zip_file.read("data/manual/test_webhook/webhook1.txt").decode("utf-8")
                == "webhook content 1"
            )
            assert (
                zip_file.read("data/manual/test_webhook/webhook2.pdf")
                == b"webhook content 2"
            )
            assert (
                zip_file.read("attachments/top_level.txt").decode("utf-8")
                == "top level content"
            )

            # Verify that the manual webhook page contains clickable links to its attachments
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )
            assert 'href="webhook1.txt"' in manual_data
            assert 'href="webhook2.pdf"' in manual_data
            assert 'class="attachment-link"' in manual_data
            assert (
                'href="top_level.txt"' not in manual_data
            )  # Top-level attachment shouldn't be linked

            # Verify that the attachments index page only contains top-level attachments
            attachments_index = zip_file.read("attachments/index.html").decode("utf-8")
            assert (
                "webhook1.txt" not in attachments_index
            )  # Webhook attachments shouldn't be in index
            assert (
                "webhook2.pdf" not in attachments_index
            )  # Webhook attachments shouldn't be in index
            assert (
                "top_level.txt" in attachments_index
            )  # Only top-level attachment should be in index

    def test_with_multiple_manual_webhooks(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with multiple manual webhooks and their attachments"""
        dsr_data = {
            "test_webhook": [
                {
                    "email": "test@example.com",
                    "last_name": "Test User",
                    "attachments": [
                        {
                            "file_name": "webhook1.txt",
                            "file_size": 1024,
                            "content_type": "text/plain",
                            "content": "webhook content 1",
                            "download_url": "http://example.com/webhook1.txt",
                        }
                    ],
                    "system_name": "test_system",
                }
            ],
            "test_webhook2": [
                {
                    "phone": "+1234567890",
                    "attachments": [
                        {
                            "file_name": "webhook2.pdf",
                            "file_size": 2048,
                            "content_type": "application/pdf",
                            "content": b"webhook content 2",
                            "download_url": "http://example.com/webhook2.pdf",
                        }
                    ],
                    "system_name": "test_system2",
                }
            ],
            "attachments": [
                {
                    "file_name": "top_level.txt",
                    "file_size": 3072,
                    "content_type": "text/plain",
                    "content": "top level content",
                    "download_url": "http://example.com/top_level.txt",
                }
            ],
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify that webhook attachments are present in both locations
            assert "attachments/webhook1.txt" in zip_file.namelist()
            assert "attachments/webhook2.pdf" in zip_file.namelist()
            assert "data/test_system/test_webhook/webhook1.txt" in zip_file.namelist()
            assert "data/test_system2/test_webhook2/webhook2.pdf" in zip_file.namelist()

            # Verify that top-level attachment is only in attachments directory
            assert "attachments/top_level.txt" in zip_file.namelist()
            assert "data/test_system/test_webhook/top_level.txt" not in zip_file.namelist()
            assert "data/test_system2/test_webhook2/top_level.txt" not in zip_file.namelist()

            # Verify attachment content in both locations
            assert (
                zip_file.read("attachments/webhook1.txt").decode("utf-8")
                == "webhook content 1"
            )
            assert zip_file.read("attachments/webhook2.pdf") == b"webhook content 2"
            assert (
                zip_file.read("data/test_system/test_webhook/webhook1.txt").decode("utf-8")
                == "webhook content 1"
            )
            assert (
                zip_file.read("data/test_system2/test_webhook2/webhook2.pdf")
                == b"webhook content 2"
            )
            assert (
                zip_file.read("attachments/top_level.txt").decode("utf-8")
                == "top level content"
            )

            # Verify that the manual webhook pages contain clickable links to their attachments
            webhook1_data = zip_file.read("data/test_system/test_webhook/1.html").decode("utf-8")
            assert 'href="webhook1.txt"' in webhook1_data
            assert 'class="attachment-link"' in webhook1_data
            assert "test@example.com" in webhook1_data
            assert "Test User" in webhook1_data
            assert "test_system" in webhook1_data

            webhook2_data = zip_file.read("data/test_system2/test_webhook2/1.html").decode("utf-8")
            assert 'href="webhook2.pdf"' in webhook2_data
            assert 'class="attachment-link"' in webhook2_data
            assert "+1234567890" in webhook2_data
            assert "test_system2" in webhook2_data

            # Verify that the attachments index page only contains top-level attachment
            attachments_index = zip_file.read("attachments/index.html").decode("utf-8")
            assert "webhook1.txt" not in attachments_index  # Webhook attachments shouldn't be in index
            assert "webhook2.pdf" not in attachments_index  # Webhook attachments shouldn't be in index
            assert "top_level.txt" in attachments_index  # Only top-level attachment should be in index


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
            collection1_content = zip_file.read("data/dataset1/collection1/index.html").decode("utf-8")
            assert "Item 1" in collection1_content
            assert "Item 2" in collection1_content

            collection2_content = zip_file.read("data/dataset1/collection2/index.html").decode("utf-8")
            assert "Item 3" in collection2_content

            collection3_content = zip_file.read("data/dataset2/collection1/index.html").decode("utf-8")
            assert "Item 4" in collection3_content

    def test_with_large_data(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with large data sets"""
        # Create a large dataset with many items
        dsr_data = {
            "dataset1:collection1": [
                {"id": i, "name": f"Item {i}", "data": "x" * 1000}  # 1KB per item
                for i in range(100)  # 100 items = ~100KB
            ]
        }

        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Verify collection index page exists
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()

            # Verify all items are in the collection index page
            collection_content = zip_file.read("data/dataset1/collection1/index.html").decode("utf-8")
            for i in range(100):
                assert f"Item {i}" in collection_content

            # Verify index pages
            assert "data/dataset1/index.html" in zip_file.namelist()


class TestDsrReportBuilderDataTypes:
    """Tests for DSR report builder's data type handling"""

    @staticmethod
    def extract_table_values(html_content: str) -> Dict[str, str]:
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
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )

            # Extract all values from the table
            table_values = self.extract_table_values(manual_data)

            # Verify each value is present and properly formatted
            assert "test string" in table_values["string_field"]
            assert "123" in table_values["number_field"]
            assert "123.45" in table_values["float_field"]
            assert "true" in table_values["boolean_field"]
            assert "null" in table_values["null_field"]
            assert "2024-01-01T00:00:00" in table_values["date_field"]

            # For list and dict fields, we check that they contain the expected elements
            # rather than matching the exact string representation
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
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )

            # Extract all values from the table
            table_values = self.extract_table_values(manual_data)

            # Verify each value is present and properly escaped
            assert "test@example.com" in table_values["email"]

            # For special characters, we check that each character is present
            # rather than matching the exact escaped string
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


class TestDsrReportBuilder:
    def test_generate_report_structure(self, privacy_request, dsr_data: dict):
        """Test that the generated report has the correct structure"""
        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        # Verify it's a valid zip file
        with zipfile.ZipFile(report) as zip_file:
            # Check for required files
            assert "welcome.html" in zip_file.namelist()
            assert "data/main.css" in zip_file.namelist()
            assert "data/back.svg" in zip_file.namelist()

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
            assert "Your requested data" in welcome_content
            assert "dataset1" in welcome_content

            # Check dataset index content
            dataset1_content = zip_file.read("data/dataset1/index.html").decode("utf-8")
            assert "dataset1" in dataset1_content
            assert "collection1" in dataset1_content

            # Check collection index content
            collection1_content = zip_file.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            assert "collection1" in collection1_content
            assert "item #1" in collection1_content
            assert "item #2" in collection1_content
            assert "item1@example.com" in collection1_content
            assert "Item 1" in collection1_content

    def test_empty_dsr_data(self, privacy_request):
        """Test report generation with empty DSR data"""
        builder = DsrReportBuilder(privacy_request, {})
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            assert "welcome.html" in zip_file.namelist()
            assert "data/main.css" in zip_file.namelist()
            assert "data/back.svg" in zip_file.namelist()
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
            assert str(privacy_request.id) in welcome_content
            assert privacy_request.policy.get_action_type().value in welcome_content
            assert (
                privacy_request.requested_at.strftime("%m/%d/%Y %H:%M %Z")
                in welcome_content
            )

    def test_dataset_ordering(self, privacy_request):
        """Test that regular datasets are alphabetical with Additional Data and Additional Attachments last"""
        dsr_data = {
            "zebra:collection1": [{"id": 1}],
            "attachments": [{"file_name": "test.txt", "content": "test"}],
            "alpha:collection1": [{"id": 2}],
            "beta:collection1": [{"id": 3}],
            "dataset:collection1": [{"id": 4}],  # This should be renamed to "Additional Data"
            "charlie:collection1": [{"id": 5}],
        }

        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            welcome_content = zip_file.read("welcome.html").decode("utf-8")

            # Find the order of links in the welcome page
            link_order = []
            for line in welcome_content.split("\n"):
                if 'href="data/' in line or 'href="attachments/' in line:
                    if 'data/alpha/' in line:
                        link_order.append("alpha")
                    elif 'data/beta/' in line:
                        link_order.append("beta")
                    elif 'data/charlie/' in line:
                        link_order.append("charlie")
                    elif 'data/zebra/' in line:
                        link_order.append("zebra")
                    elif 'data/dataset/' in line:
                        link_order.append("Additional Data")
                    elif 'attachments/index.html' in line:
                        link_order.append("Additional Attachments")

            # Verify the order: regular datasets alphabetically, then Additional Data, then Additional Attachments
            assert link_order == [
                "alpha",
                "beta",
                "charlie",
                "zebra",
                "Additional Data",
                "Additional Attachments"
            ]

            # Verify the dataset directory structure
            assert "data/dataset/index.html" in zip_file.namelist()  # Original directory name
            assert "data/dataset/collection1/index.html" in zip_file.namelist()

            # Verify the welcome page shows "Additional Data" instead of "dataset"
            assert "Additional Data" in welcome_content
            assert "dataset" not in welcome_content  # Should not appear as a link text


class TestDsrReportBuilderAttachmentHandling:
    """Tests for DSR report builder's attachment handling functions"""

    def test_handle_attachment_text(self, privacy_request: PrivacyRequest):
        """Test handling a text attachment"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachment = {
            "file_name": "test.txt",
            "content": "test content",
            "content_type": "text/plain"
        }

        builder._handle_attachment(attachment, "dataset1", "collection1")

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Check only collection directory location
            assert "data/dataset1/collection1/test.txt" in zip_file.namelist()
            assert "attachments/test.txt" not in zip_file.namelist()

            # Verify content
            content = zip_file.read("data/dataset1/collection1/test.txt").decode("utf-8")
            assert content == "test content"

    def test_handle_attachment_binary(self, privacy_request: PrivacyRequest):
        """Test handling a binary attachment"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachment = {
            "file_name": "test.pdf",
            "content": b"test content",
            "content_type": "application/pdf"
        }

        builder._handle_attachment(attachment, "dataset1", "collection1")

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Check only collection directory location
            assert "data/dataset1/collection1/test.pdf" in zip_file.namelist()
            assert "attachments/test.pdf" not in zip_file.namelist()

            # Verify content
            content = zip_file.read("data/dataset1/collection1/test.pdf")
            assert content == b"test content"

    def test_handle_attachment_no_content(self, privacy_request: PrivacyRequest):
        """Test handling an attachment with no content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachment = {
            "file_name": "test.txt",
            "content": None,
            "content_type": "text/plain"
        }

        builder._handle_attachment(attachment, "dataset1", "collection1")

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "data/dataset1/collection1/test.txt" not in zip_file.namelist()

    def test_add_attachments_top_level(self, privacy_request: PrivacyRequest):
        """Test adding top-level attachments"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            {
                "file_name": "test1.txt",
                "content": "content1",
                "content_type": "text/plain"
            },
            {
                "file_name": "test2.pdf",
                "content": b"content2",
                "content_type": "application/pdf"
            }
        ]

        builder._add_attachments(attachments)

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            # Check attachments directory
            assert "attachments/test1.txt" in zip_file.namelist()
            assert "attachments/test2.pdf" in zip_file.namelist()
            assert "attachments/index.html" in zip_file.namelist()

            # Verify content
            assert zip_file.read("attachments/test1.txt").decode("utf-8") == "content1"
            assert zip_file.read("attachments/test2.pdf") == b"content2"

            # Verify index page
            index_content = zip_file.read("attachments/index.html").decode("utf-8")
            assert "test1.txt" in index_content
            assert "test2.pdf" in index_content

    def test_add_attachments_empty(self, privacy_request: PrivacyRequest):
        """Test adding empty attachments list"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        builder._add_attachments([])

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert not any(name.startswith("attachments/") for name in zip_file.namelist())

    def test_add_attachments_invalid(self, privacy_request: PrivacyRequest):
        """Test adding invalid attachments"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        attachments = [
            None,
            "not a dict",
            {"file_name": "test.txt"},  # Missing content
            {"content": "test"},  # Missing file_name
        ]

        builder._add_attachments(attachments)

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert not any(name.startswith("attachments/") for name in zip_file.namelist())


class TestDsrReportBuilderItemProcessing:
    """Tests for DSR report builder's item processing functions"""

    def test_process_item_attachments(self, privacy_request: PrivacyRequest):
        """Test processing attachments in an item"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        item = {
            "id": 1,
            "attachments": [
                {
                    "file_name": "test1.txt",
                    "content": "content1",
                    "content_type": "text/plain"
                },
                {
                    "file_name": "test2.pdf",
                    "content": b"content2",
                    "content_type": "application/pdf"
                }
            ]
        }

        builder._process_item_attachments(item, "dataset1", "collection1")

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "attachments/test1.txt" in zip_file.namelist()
            assert "attachments/test2.pdf" in zip_file.namelist()
            assert "data/dataset1/collection1/test1.txt" in zip_file.namelist()
            assert "data/dataset1/collection1/test2.pdf" in zip_file.namelist()

    def test_process_item_no_attachments(self, privacy_request: PrivacyRequest):
        """Test processing an item with no attachments"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        item = {"id": 1}

        builder._process_item_attachments(item, "dataset1", "collection1")

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert not any(name.startswith("attachments/") for name in zip_file.namelist())
            assert not any(name.startswith("data/dataset1/collection1/") for name in zip_file.namelist())

    def test_prepare_item_content(self, privacy_request: PrivacyRequest):
        """Test preparing item content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        item = {"id": 1, "name": "Test Item"}

        content = builder._prepare_item_content(item, 1, "collection1")

        assert content["index"] == 1
        assert content["heading"] == "collection1 (item #1)"
        assert content["data"] == item

    def test_generate_collection_index(self, privacy_request: PrivacyRequest):
        """Test generating collection index page"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        items_content = [
            {
                "index": 1,
                "heading": "collection1 (item #1)",
                "data": {"id": 1, "name": "Item 1"}
            },
            {
                "index": 2,
                "heading": "collection1 (item #2)",
                "data": {"id": 2, "name": "Item 2"}
            }
        ]

        builder._generate_collection_index("dataset1", "collection1", items_content)

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()
            content = zip_file.read("data/dataset1/collection1/index.html").decode("utf-8")
            assert "collection1" in content
            assert "Item 1" in content
            assert "Item 2" in content


class TestDsrReportBuilderTemplateHandling:
    """Tests for DSR report builder's template handling functions"""

    def test_populate_template(self, privacy_request: PrivacyRequest):
        """Test populating a template with data"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        data = {"test_key": "test_value"}

        result = builder._populate_template(
            "templates/collection_index.html",
            "Test Heading",
            "Test Description",
            data
        )

        assert "Test Heading" in result
        assert "Test Description" in result
        assert "test_key" in result
        assert "test_value" in result

    def test_populate_template_no_data(self, privacy_request: PrivacyRequest):
        """Test populating a template with no data"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        result = builder._populate_template(
            "templates/collection_index.html",
            "Test Heading"
        )

        assert "Test Heading" in result
        assert "data" not in result

    def test_add_file(self, privacy_request: PrivacyRequest):
        """Test adding a file to the zip"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        content = "test content"

        builder._add_file("test.txt", content)

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "test.txt" in zip_file.namelist()
            assert zip_file.read("test.txt").decode("utf-8") == content

    def test_add_file_empty_content(self, privacy_request: PrivacyRequest):
        """Test adding a file with empty content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        builder._add_file("test.txt", "")

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "test.txt" not in zip_file.namelist()


class TestDsrReportBuilderDatasetHandling:
    """Tests for DSR report builder's dataset handling functions"""

    def test_add_dataset(self, privacy_request: PrivacyRequest):
        """Test adding a dataset with collections"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})
        collections = {
            "collection1": [{"id": 1}, {"id": 2}],
            "collection2": [{"id": 3}]
        }

        builder._add_dataset("dataset1", collections)

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

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "data/dataset1/index.html" in zip_file.namelist()
            content = zip_file.read("data/dataset1/index.html").decode("utf-8")
            assert "dataset1" in content
            assert "collection" not in content


class TestDsrReportBuilderAttachmentContentWriting:
    """Tests for DSR report builder's attachment content writing functionality"""

    def test_write_text_attachment_content(self, privacy_request: PrivacyRequest):
        """Test writing text-based attachment content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Test text/plain
        builder._write_attachment_content(
            "test.txt",
            "test content",
            "text/plain",
            "attachments"
        )

        # Test text/csv
        builder._write_attachment_content(
            "test.csv",
            "header1,header2\nvalue1,value2",
            "text/csv",
            "attachments"
        )

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "attachments/test.txt" in zip_file.namelist()
            assert "attachments/test.csv" in zip_file.namelist()
            assert zip_file.read("attachments/test.txt").decode("utf-8") == "test content"
            assert zip_file.read("attachments/test.csv").decode("utf-8") == "header1,header2\nvalue1,value2"

    def test_write_image_attachment_content(self, privacy_request: PrivacyRequest):
        """Test writing image attachment content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Test image/jpeg
        jpeg_content = b"fake jpeg content"
        builder._write_attachment_content(
            "test.jpg",
            jpeg_content,
            "image/jpeg",
            "attachments"
        )

        # Test image/png
        png_content = b"fake png content"
        builder._write_attachment_content(
            "test.png",
            png_content,
            "image/png",
            "attachments"
        )

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "attachments/test.jpg" in zip_file.namelist()
            assert "attachments/test.png" in zip_file.namelist()
            assert zip_file.read("attachments/test.jpg") == jpeg_content
            assert zip_file.read("attachments/test.png") == png_content

    def test_write_document_attachment_content(self, privacy_request: PrivacyRequest):
        """Test writing document attachment content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Test PDF
        pdf_content = b"fake pdf content"
        builder._write_attachment_content(
            "test.pdf",
            pdf_content,
            "application/pdf",
            "attachments"
        )

        # Test Word document
        doc_content = b"fake word content"
        builder._write_attachment_content(
            "test.docx",
            doc_content,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "attachments"
        )

        # Test Excel document
        xlsx_content = b"fake excel content"
        builder._write_attachment_content(
            "test.xlsx",
            xlsx_content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "attachments"
        )

        # Test ZIP file
        zip_content = b"fake zip content"
        builder._write_attachment_content(
            "test.zip",
            zip_content,
            "application/zip",
            "attachments"
        )

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "attachments/test.pdf" in zip_file.namelist()
            assert "attachments/test.docx" in zip_file.namelist()
            assert "attachments/test.xlsx" in zip_file.namelist()
            assert "attachments/test.zip" in zip_file.namelist()
            assert zip_file.read("attachments/test.pdf") == pdf_content
            assert zip_file.read("attachments/test.docx") == doc_content
            assert zip_file.read("attachments/test.xlsx") == xlsx_content
            assert zip_file.read("attachments/test.zip") == zip_content

    def test_write_attachment_content_no_content(self, privacy_request: PrivacyRequest):
        """Test writing attachment content with no content"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        builder._write_attachment_content(
            "test.txt",
            None,
            "text/plain",
            "attachments"
        )

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "attachments/test.txt" not in zip_file.namelist()

    def test_write_attachment_content_different_directories(self, privacy_request: PrivacyRequest):
        """Test writing attachment content to different directories"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Write to attachments directory
        builder._write_attachment_content(
            "test.txt",
            "test content",
            "text/plain",
            "attachments"
        )

        # Write to collection directory
        builder._write_attachment_content(
            "test.txt",
            "test content",
            "text/plain",
            "data/dataset1/collection1"
        )

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "attachments/test.txt" in zip_file.namelist()
            assert "data/dataset1/collection1/test.txt" in zip_file.namelist()
            assert zip_file.read("attachments/test.txt").decode("utf-8") == "test content"
            assert zip_file.read("data/dataset1/collection1/test.txt").decode("utf-8") == "test content"

    def test_write_attachment_content_type_conversion(self, privacy_request: PrivacyRequest):
        """Test writing attachment content with type conversion"""
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data={})

        # Test string to bytes conversion for binary content
        builder._write_attachment_content(
            "test.pdf",
            "fake pdf content",
            "application/pdf",
            "attachments"
        )

        # Test bytes to string conversion for text content
        builder._write_attachment_content(
            "test.txt",
            b"fake text content",
            "text/plain",
            "attachments"
        )

        with zipfile.ZipFile(io.BytesIO(builder.baos.getvalue())) as zip_file:
            assert "attachments/test.pdf" in zip_file.namelist()
            assert "attachments/test.txt" in zip_file.namelist()
            assert zip_file.read("attachments/test.pdf") == b"fake pdf content"
            assert zip_file.read("attachments/test.txt").decode("utf-8") == "fake text content"
