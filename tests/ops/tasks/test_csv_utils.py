import zipfile
from io import BytesIO

import pandas as pd

from fides.api.tasks.csv_utils import (
    _write_attachment_csv,
    _write_item_csv,
    _write_simple_csv,
    create_attachment_csv,
    create_csv_from_dataframe,
    write_csv_to_zip,
)


class TestCreateCSVFromDataFrame:
    def test_create_csv_from_dataframe(self):
        df = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})

        result = create_csv_from_dataframe(df)

        assert isinstance(result, BytesIO)
        content = result.getvalue().decode()
        assert "name,age" in content
        assert "John,30" in content
        assert "Jane,25" in content


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
            assert "users.csv" in zip_file.namelist()
            assert "users/1/attachments.csv" in zip_file.namelist()

            # Verify the content of users.csv
            content = zip_file.read("users.csv").decode()
            assert "name,age" in content
            assert "John,30" in content


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
        items = [{"name": "John", "age": 30}]

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            _write_item_csv(zip_file, "test", items, "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "test.csv" in zip_file.namelist()
            content = zip_file.read("test.csv").decode()
            assert "name,age" in content
            assert "John,30" in content

    def test_write_item_csv_empty(self):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            _write_item_csv(zip_file, "test", [], "test-request-id")

        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            assert "test.csv" not in zip_file.namelist()


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
