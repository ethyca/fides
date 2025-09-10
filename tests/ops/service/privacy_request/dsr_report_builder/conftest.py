import re
from io import BytesIO

import pytest

DSR_DATA_DUPLICATE_FILE_NAMES = {
    "manualtask:manual_data": [
        {
            "accesstest": [
                {
                    "file_name": "test_file_text.txt",
                    "download_url": "https://example-bucket.s3.amazonaws.com/att_a60d13cc-e6ca-4783-ac7c-5539e4f68584/test_file_text.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA5P2TGBOOU4X5T5NS%2F20250903%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250903T082813Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=3e315fe8b00262867eecc9b031c5ccc7f21fee3e095c181a9bf1b73c8c04952e",
                    "file_size": 46,
                }
            ]
        }
    ],
    "manualtask2:manual_data": [
        {
            "accesstest2": [
                {
                    "file_name": "test_file_pdf.pdf",
                    "download_url": "https://example-bucket.s3.amazonaws.com/att_2f8e58ac-54a8-4584-a93e-25d4b27d65b1/test_file_pdf.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA5P2TGBOOU4X5T5NS%2F20250903%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250903T082801Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=bc3c041750f562e24d8c13a76698e9079334f7cad3f2d3ed56c9a1343f25ad8f",
                    "file_size": 11236,
                },
                {
                    "file_name": "test_file_text.txt",
                    "download_url": "https://example-bucket.s3.amazonaws.com/att_16edd701-8b7c-4276-b1d8-975cb32cabd5/test_file_text.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA5P2TGBOOU4X5T5NS%2F20250903%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250903T082802Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=9ef7145e407c460dd75d5a013f1c4eb3f7abb41c7d66931915fc3927becf84e4",
                    "file_size": 29,
                },
                {
                    "file_name": "test_file_text.txt",
                    "download_url": "https://example-bucket.s3.amazonaws.com/att_9ec66e19-458f-4fe6-8b72-6b9e112b05bf/test_file_text.txt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA5P2TGBOOU4X5T5NS%2F20250903%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250903T082803Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=92482f3dd3043ec28fdba554abdca277eb013c189bfcd9d50db1fda9bd974790",
                    "file_size": 41,
                },
            ]
        }
    ],
}


@pytest.fixture
def dsr_data_duplicate_file_names():
    return DSR_DATA_DUPLICATE_FILE_NAMES


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

        for key_cell, value_cell in rows:
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
