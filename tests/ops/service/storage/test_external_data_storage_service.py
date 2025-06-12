import os

import pytest

from fides.api.schemas.external_storage import ExternalStorageMetadata
from fides.api.service.external_data_storage import (
    ExternalDataStorageError,
    ExternalDataStorageService,
)
from fides.api.service.storage.util import get_local_filename


class TestExternalDataStorageService:
    """
    Testing only with local storage, this isn't a comprehensive test of
    the various storage providers just the ExternalDataStorageService logic
    """

    def test_store_data_with_default_storage_config(self, db):
        """Test storing data using default storage configuration"""
        test_data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
        storage_path = "test/data/test_file"

        metadata = ExternalDataStorageService.store_data(
            db=db, storage_path=storage_path, data=test_data
        )

        assert metadata is not None
        assert isinstance(metadata, ExternalStorageMetadata)
        assert metadata.storage_type == "local"
        assert metadata.file_key == storage_path
        assert metadata.filesize > 0
        assert (
            metadata.storage_key == "default_storage_config_local"
        )  # auto-created by the app code

        # Verify file was created
        file_path = get_local_filename(storage_path)
        assert os.path.exists(file_path)

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_store_data_with_specific_storage_key(self, db, storage_config_local):
        """Test storing data using a specific storage configuration key"""
        test_data = {"key": "value", "nested": {"data": [1, 2, 3]}}
        storage_path = "test/data/test_file"

        metadata = ExternalDataStorageService.store_data(
            db=db,
            storage_path=storage_path,
            data=test_data,
            storage_key=storage_config_local.key,
        )

        assert metadata is not None
        assert metadata.storage_type == "local"
        assert metadata.file_key == storage_path
        assert metadata.storage_key == storage_config_local.key
        assert metadata.filesize > 0

        # Verify file was created
        file_path = get_local_filename(storage_path)
        assert os.path.exists(file_path)

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_retrieve_data_success(self, db):
        """Test successful data retrieval from external storage"""
        original_data = [
            {"id": 1, "name": "Charlie", "active": True},
            {"id": 2, "name": "Diana", "active": False},
        ]
        storage_path = "test/data/test_file"

        # Store data first
        metadata = ExternalDataStorageService.store_data(
            db=db, storage_path=storage_path, data=original_data
        )

        retrieved_data = ExternalDataStorageService.retrieve_data(
            db=db, metadata=metadata
        )

        assert retrieved_data == original_data
        assert len(retrieved_data) == 2
        assert retrieved_data[0]["name"] == "Charlie"
        assert retrieved_data[1]["active"] is False

        # Cleanup
        file_path = get_local_filename(storage_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_delete_data_success(self, db):
        """Test successful deletion of external storage files"""
        test_data = {"message": "This will be deleted"}
        storage_path = "test/data/test_file"

        # Store data first
        metadata = ExternalDataStorageService.store_data(
            db=db, storage_path=storage_path, data=test_data
        )

        file_path = get_local_filename(storage_path)
        assert os.path.exists(file_path)  # Verify file exists before deletion

        ExternalDataStorageService.delete_data(db=db, metadata=metadata)

        assert not os.path.exists(file_path)  # File should be deleted

    def test_store_retrieve_delete_cycle(
        self,
        db,
    ):
        """Test complete lifecycle: store -> retrieve -> delete"""
        test_data = {
            "users": [
                {
                    "id": 1,
                    "name": "Eva",
                    "preferences": {"theme": "dark", "notifications": True},
                },
                {
                    "id": 2,
                    "name": "Frank",
                    "preferences": {"theme": "light", "notifications": False},
                },
            ],
            "metadata": {"total_count": 2, "last_updated": "2024-01-01T00:00:00Z"},
        }
        storage_path = "test/data/test_file"

        metadata = ExternalDataStorageService.store_data(
            db=db, storage_path=storage_path, data=test_data
        )

        assert metadata is not None
        assert metadata.file_key == storage_path
        file_path = get_local_filename(storage_path)
        assert os.path.exists(file_path)

        retrieved_data = ExternalDataStorageService.retrieve_data(
            db=db, metadata=metadata
        )

        assert retrieved_data == test_data
        assert len(retrieved_data["users"]) == 2
        assert retrieved_data["metadata"]["total_count"] == 2
        assert retrieved_data["users"][0]["preferences"]["theme"] == "dark"

        ExternalDataStorageService.delete_data(db=db, metadata=metadata)

        assert not os.path.exists(file_path)

    def test_store_data_invalid_storage_key_raises_error(self, db):
        """Test storing data with non-existent storage key"""
        test_data = {"test": "data"}
        storage_path = "test/data/test_file"
        invalid_key = "nonexistent_storage_key"

        with pytest.raises(
            ExternalDataStorageError,
            match=f"Storage configuration with key '{invalid_key}' not found",
        ):
            ExternalDataStorageService.store_data(
                db=db,
                storage_path=storage_path,
                data=test_data,
                storage_key=invalid_key,
            )

    def test_retrieve_data_file_not_found_raises_error(self, db, storage_config_local):
        """Test retrieving data when external file doesn't exist"""
        fake_metadata = ExternalStorageMetadata(
            storage_type="local",
            file_key="nonexistent/path/test_file",
            filesize=1000,
            storage_key=storage_config_local.key,
        )

        with pytest.raises(ExternalDataStorageError, match="Failed to retrieve data"):
            ExternalDataStorageService.retrieve_data(db=db, metadata=fake_metadata)

    def test_store_retrieve_preserves_data_integrity(self, db):
        """Test that stored and retrieved data is identical for complex structures"""
        complex_data = {
            "simple_string": "hello world",
            "unicode_string": "héllo wørld 🌍",
            "numbers": [1, 2.5, -3, 0],
            "booleans": [True, False],
            "nested_dict": {
                "level1": {"level2": {"deep_list": [{"item": i} for i in range(5)]}}
            },
            "mixed_list": ["string", 42, {"nested": True}, [1, 2, 3]],
            "null_value": None,
            "empty_structures": {"empty_list": [], "empty_dict": {}},
        }
        storage_path = "test/data/test_file"

        metadata = ExternalDataStorageService.store_data(
            db=db, storage_path=storage_path, data=complex_data
        )

        retrieved_data = ExternalDataStorageService.retrieve_data(
            db=db, metadata=metadata
        )

        assert retrieved_data == complex_data

        ExternalDataStorageService.delete_data(db=db, metadata=metadata)

    def test_store_retrieve_empty_data_structures(self, db, storage_config_local):
        """Test with empty lists, dicts, and None values"""
        empty_data_cases = [
            [],
            {},
            None,
            [{}],
            {"empty": []},
        ]

        for i, test_data in enumerate(empty_data_cases):
            storage_path = f"test/data/test_file"

            metadata = ExternalDataStorageService.store_data(
                db=db, storage_path=storage_path, data=test_data
            )

            retrieved_data = ExternalDataStorageService.retrieve_data(
                db=db, metadata=metadata
            )

            assert retrieved_data == test_data

            ExternalDataStorageService.delete_data(db=db, metadata=metadata)

    def test_metadata_contains_correct_information(self, db, storage_config_local):
        """Test metadata includes correct storage type, file size, and storage key"""
        test_data = {"message": "testing metadata"}
        storage_path = "test/data/test_file"

        metadata = ExternalDataStorageService.store_data(
            db=db,
            storage_path=storage_path,
            data=test_data,
            storage_key=storage_config_local.key,
        )

        assert metadata.storage_type == "local"
        assert metadata.file_key == storage_path
        assert metadata.storage_key == storage_config_local.key
        assert metadata.filesize > 0

        # Verify the file size matches actual file size
        file_path = get_local_filename(storage_path)
        actual_file_size = os.path.getsize(file_path)
        assert metadata.filesize == actual_file_size

        ExternalDataStorageService.delete_data(db=db, metadata=metadata)
