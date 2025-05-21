import io
import json
import zipfile
from datetime import datetime
from typing import Dict, List

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)


class TestDsrReportBuilderAttachments:
    """Tests for DSR report builder's attachment handling"""

    def test_with_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with attachments in manual webhook data"""
        # Create test data with attachments in different locations
        dsr_data = {
            "manual:test_webhook": [
                {
                    "email": "test@example.com",
                    "attachments": [
                        {
                            "file_name": "test1.pdf",
                            "file_size": 1024,
                            "content_type": "application/pdf",
                            "content": b"test content 1",
                            "download_url": "http://example.com/test1.pdf",
                        }
                    ],
                    "nested_data": {
                        "attachments": [
                            {
                                "file_name": "test2.pdf",
                                "file_size": 2048,
                                "content_type": "application/pdf",
                                "content": b"test content 2",
                                "download_url": "http://example.com/test2.pdf",
                            }
                        ]
                    },
                }
            ],
            "attachments": [
                {
                    "file_name": "test3.pdf",
                    "file_size": 3072,
                    "content_type": "application/pdf",
                    "content": b"test content 3",
                    "download_url": "http://example.com/test3.pdf",
                }
            ],
        }

        # Create the DSR report
        builder = DsrReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        # Verify the report structure
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            # Check that all attachment files are present
            assert "data/attachments/files/test1.pdf" in zip_file.namelist()
            assert "data/attachments/files/test2.pdf" in zip_file.namelist()
            assert "data/attachments/files/test3.pdf" in zip_file.namelist()

            # Check that attachment metadata pages are present
            assert "data/attachments/1.html" in zip_file.namelist()
            assert "data/attachments/2.html" in zip_file.namelist()
            assert "data/attachments/3.html" in zip_file.namelist()
            assert "data/attachments/index.html" in zip_file.namelist()

            # Verify attachment content
            assert (
                zip_file.read("data/attachments/files/test1.pdf") == b"test content 1"
            )
            assert (
                zip_file.read("data/attachments/files/test2.pdf") == b"test content 2"
            )
            assert (
                zip_file.read("data/attachments/files/test3.pdf") == b"test content 3"
            )

            # Verify that attachments were removed from manual data
            manual_data = zip_file.read("data/manual/test_webhook/1.html").decode(
                "utf-8"
            )
            assert "attachments" not in manual_data
            assert "test@example.com" in manual_data

    def test_without_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with no attachments"""
        dsr_data = {
            "manual:test_webhook": [{"email": "test@example.com", "name": "Test User"}]
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
            assert "Test User" in manual_data

    def test_with_empty_attachments(self, privacy_request: PrivacyRequest):
        """Test DSR report builder with empty attachment lists"""
        dsr_data = {
            "manual:test_webhook": [
                {
                    "email": "test@example.com",
                    "attachments": [],
                    "nested_data": {"attachments": []},
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
                name.startswith("data/attachments/") for name in zip_file.namelist()
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

            # Verify item pages
            assert "data/dataset1/collection1/1.html" in zip_file.namelist()
            assert "data/dataset1/collection1/2.html" in zip_file.namelist()
            assert "data/dataset1/collection2/1.html" in zip_file.namelist()
            assert "data/dataset2/collection1/1.html" in zip_file.namelist()

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
            # Verify all items were included
            for i in range(100):
                assert f"data/dataset1/collection1/{i+1}.html" in zip_file.namelist()

            # Verify index pages
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()


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
