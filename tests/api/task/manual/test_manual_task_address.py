import pytest
from pytest import param

from fides.api.graph.config import CollectionAddress
from fides.api.task.manual.manual_task_address import ManualTaskAddress


class TestManualTaskAddress:
    """Test ManualTaskAddress utility class methods"""

    def test_create_manual_task_address(self):
        """Test creating manual task addresses"""
        address = ManualTaskAddress.create("postgres_connection")
        assert address.dataset == "postgres_connection"
        assert address.collection == "manual_data"

    def test_is_manual_task_address(self):
        """Test detecting manual task addresses"""
        manual_address = CollectionAddress("postgres_connection", "manual_data")
        regular_address = CollectionAddress("postgres_connection", "users")

        assert ManualTaskAddress.is_manual_task_address(manual_address) == True
        assert ManualTaskAddress.is_manual_task_address(regular_address) == False

    def test_is_manual_task_address_with_string(self):
        """Test detecting manual task addresses with string format"""
        manual_address = "postgres_connection:manual_data"
        regular_address = "postgres_connection:users"

        assert ManualTaskAddress.is_manual_task_address(manual_address) == True
        assert ManualTaskAddress.is_manual_task_address(regular_address) == False

    def test_get_connection_key(self):
        """Test extracting connection key from manual task address"""
        address = CollectionAddress("postgres_connection", "manual_data")
        key = ManualTaskAddress.get_connection_key(address)
        assert key == "postgres_connection"

    def test_get_connection_key_with_string(self):
        """Test extracting connection key from string format address"""
        address = "postgres_connection:manual_data"
        key = ManualTaskAddress.get_connection_key(address)
        assert key == "postgres_connection"

    def test_get_connection_key_raises_error_for_invalid_address(self):
        """Test that get_connection_key raises error for invalid addresses"""
        bad_address = CollectionAddress("postgres_connection", "users")
        with pytest.raises(ValueError, match="Not a manual task address"):
            ManualTaskAddress.get_connection_key(bad_address)

    def test_manual_data_collection_constant(self):
        """Test that the MANUAL_DATA_COLLECTION constant is correct"""
        assert ManualTaskAddress.MANUAL_DATA_COLLECTION == "manual_data"

    def test_is_manual_data_collection(self):
        """Test the _is_manual_data_collection helper method"""
        # Only "manual_data" is valid now
        assert ManualTaskAddress._is_manual_data_collection("manual_data") == True

        # Invalid collections
        assert (
            ManualTaskAddress._is_manual_data_collection("manual_data_task_123")
            == False
        )
        assert (
            ManualTaskAddress._is_manual_data_collection("manual_data_abc-def") == False
        )
        assert ManualTaskAddress._is_manual_data_collection("other_collection") == False
        assert ManualTaskAddress._is_manual_data_collection("users") == False
        assert ManualTaskAddress._is_manual_data_collection("") == False

    def test_is_manual_task_address_string_no_colon(self):
        """Test detecting manual task addresses with string format that has no colon"""
        address_without_colon = "postgres_connection"
        assert ManualTaskAddress.is_manual_task_address(address_without_colon) == False
