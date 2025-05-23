import io
import zipfile
from io import BytesIO
from typing import Any, Dict

import pandas as pd
import pytest

from fides.api.tasks.csv_utils import (
    _write_attachment_csv,
    _write_item_csv,
    _write_simple_csv,
    create_attachment_csv,
    create_csv_from_dataframe,
    create_data_csv,
    write_csv_to_zip,
)
from fides.config import CONFIG


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "name": ["John", "Jane"],
            "age": [30, 25],
            "email": ["john@example.com", "jane@example.com"],
        }
    )


@pytest.fixture
def sample_data() -> Dict[str, Any]:
    """Create sample data for testing."""
    return {"user": {"name": "John Doe", "email": "john@example.com", "age": 30}}


@pytest.fixture
def sample_attachments() -> list:
    """Create sample attachments for testing."""
    return [
        {
            "file_name": "test1.pdf",
            "file_size": 1024,
            "content_type": "application/pdf",
            "download_url": "https://example.com/test1.pdf",
        },
        {
            "file_name": "test2.jpg",
            "file_size": 2048,
            "content_type": "image/jpeg",
            "download_url": "https://example.com/test2.jpg",
        },
    ]


def test_create_csv_from_dataframe(sample_dataframe):
    """Test creating a CSV from a DataFrame."""
    buffer = create_csv_from_dataframe(sample_dataframe)
    assert isinstance(buffer, io.BytesIO)

    # Read the CSV content
    content = buffer.getvalue().decode(CONFIG.security.encoding)
    assert "name,age,email" in content
    assert "John,30,john@example.com" in content
    assert "Jane,25,jane@example.com" in content


def test_create_data_csv(sample_data):
    """Test creating a CSV from data dictionary."""
    buffer = create_data_csv(sample_data)
    assert isinstance(buffer, io.BytesIO)

    # Read the CSV content
    content = buffer.getvalue().decode(CONFIG.security.encoding)
    assert "user.name,user.email,user.age" in content
    assert "John Doe,john@example.com,30" in content


def test_create_attachment_csv(sample_attachments):
    """Test creating a CSV from attachment data."""
    buffer = create_attachment_csv(sample_attachments)
    assert isinstance(buffer, io.BytesIO)

    # Read the CSV content
    content = buffer.getvalue().decode(CONFIG.security.encoding)
    assert "file_name,file_size,content_type,download_url" in content
    assert "test1.pdf,1024,application/pdf,https://example.com/test1.pdf" in content
    assert "test2.jpg,2048,image/jpeg,https://example.com/test2.jpg" in content


def test_create_attachment_csv_empty_list():
    """Test creating a CSV from an empty attachment list."""
    buffer = create_attachment_csv([])
    assert buffer is None


def test_write_csv_to_zip(sample_data):
    """Test writing data to a zip file in CSV format."""
    privacy_request_id = "test_request_123"

    # Create a BytesIO object to store the zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        write_csv_to_zip(zip_file, sample_data, privacy_request_id)

    # Verify the zip file contains the expected files
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        file_list = zip_file.namelist()
        assert "user.csv" in file_list

        # Read and verify the content of the CSV file
        csv_content = zip_file.read("user.csv")
        content = csv_content.decode(CONFIG.security.encoding)
        assert "user.name,user.email,user.age" in content
        assert "John Doe,john@example.com,30" in content


def test_write_csv_to_zip_with_list_data():
    """Test writing list data to a zip file in CSV format."""
    privacy_request_id = "test_request_123"
    list_data = {
        "users": [
            {
                "name": "John",
                "email": "john@example.com",
                "attachments": [
                    {
                        "file_name": "doc1.pdf",
                        "file_size": 1024,
                        "content_type": "application/pdf",
                        "download_url": "https://example.com/doc1.pdf",
                    }
                ],
            }
        ]
    }

    # Create a BytesIO object to store the zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        write_csv_to_zip(zip_file, list_data, privacy_request_id)

    # Verify the zip file contains the expected files
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        file_list = zip_file.namelist()
        assert "users/1/data.csv" in file_list
        assert "users/1/attachments.csv" in file_list


class TestCreateCSVFromDataFrame:
    def test_create_csv_from_dataframe(self):
        df = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})

        result = create_csv_from_dataframe(df)

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode()
        assert "name,age" in content
        assert "John,30" in content
        assert "Jane,25" in content


class TestCreateDataCSV:
    def test_create_data_csv(self):
        data = {
            "name": "John",
            "age": 30,
            "address": {"city": "New York", "zip": "10001"},
        }

        result = create_data_csv(data)

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode()
        assert "name,age,address.city,address.zip" in content
        assert "John,30,New York,10001" in content


class TestCreateAttachmentCSV:
    def test_create_attachment_csv_with_attachments(self):
        attachments = [
            {
                "file_name": "test1.txt",
                "file_size": 100,
                "content_type": "text/plain",
                "download_url": "http://example.com/test1.txt",
            },
            {
                "file_name": "test2.txt",
                "file_size": 200,
                "content_type": "text/plain",
                "download_url": "http://example.com/test2.txt",
            },
        ]

        result = create_attachment_csv(attachments)

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode()
        assert "file_name,file_size,content_type,download_url" in content
        assert "test1.txt,100,text/plain,http://example.com/test1.txt" in content
        assert "test2.txt,200,text/plain,http://example.com/test2.txt" in content

    def test_create_attachment_csv_empty(self):
        result = create_attachment_csv([])
        assert result is None

    def test_create_attachment_csv_invalid_data(self):
        attachments = [{"invalid": "data"}, None, "not a dict"]
        result = create_attachment_csv(attachments)
        assert result is None


class TestWriteCSVToZip:
    def test_write_csv_to_zip_simple_data(self):
        data = {"name": "John", "age": 30}

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            write_csv_to_zip(zip_file, data, "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "name.csv" in zip_file.namelist()
            assert "age.csv" in zip_file.namelist()

    def test_write_csv_to_zip_list_data(self):
        data = {
            "users": [
                {
                    "name": "John",
                    "age": 30,
                    "attachments": [{"file_name": "doc1.pdf", "file_size": 1000}],
                }
            ]
        }

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            write_csv_to_zip(zip_file, data, "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "users/1/attachments.csv" in zip_file.namelist()
            assert "users/1/data.csv" in zip_file.namelist()


class TestWriteAttachmentCSV:
    def test_write_attachment_csv(self):
        attachments = [
            {
                "file_name": "test.txt",
                "file_size": 100,
                "content_type": "text/plain",
                "download_url": "http://example.com/test.txt",
            }
        ]

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            _write_attachment_csv(zip_file, "test", 0, attachments, "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "test/1/attachments.csv" in zip_file.namelist()
            content = zip_file.read("test/1/attachments.csv").decode()
            assert "file_name,file_size,content_type,download_url" in content
            assert "test.txt,100,text/plain,http://example.com/test.txt" in content


class TestWriteItemCSV:
    def test_write_item_csv(self):
        item = {"name": "John", "age": 30}

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            _write_item_csv(zip_file, "test", 0, item, "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "test/1/data.csv" in zip_file.namelist()
            content = zip_file.read("test/1/data.csv").decode()
            assert "name,age" in content
            assert "John,30" in content

    def test_write_item_csv_empty(self):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            _write_item_csv(zip_file, "test", 0, {}, "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "test/1/data.csv" not in zip_file.namelist()


class TestWriteSimpleCSV:
    def test_write_simple_csv(self):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            _write_simple_csv(zip_file, "test", "value", "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "test.csv" in zip_file.namelist()
            content = zip_file.read("test.csv").decode()
            assert "test" in content
            assert "value" in content
