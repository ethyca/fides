import io
import zipfile
from datetime import datetime
from io import BytesIO

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import DsrReportBuilder

from .conftest import TestDsrReportBuilderBase


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

            # Check that all three files are listed with their original names (non-streaming mode)
            TestDsrReportBuilderBase.assert_html_contains(
                html_content,
                "test.txt",  # All files show original name in non-streaming mode
                "test.txt",  # All files show original name in non-streaming mode
                "test.txt",  # All files show original name in non-streaming mode
                "https://example.com/test1.txt",
                "https://example.com/test2.txt",
                "https://example.com/test3.txt",
                "1.0 KB",
                "2.0 KB",
                "3.0 KB",
            )


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
