from typing import Union

from fides.api.graph.config import CollectionAddress


class ManualTaskAddress:
    """Utility class for creating and parsing manual task addresses"""

    MANUAL_DATA_COLLECTION = "manual_data"

    @staticmethod
    def create(connection_config_key: str) -> CollectionAddress:
        """Create a CollectionAddress for manual data: {connection_key}:manual_data"""
        return CollectionAddress(
            dataset=connection_config_key,
            collection=ManualTaskAddress.MANUAL_DATA_COLLECTION,
        )

    @staticmethod
    def _is_manual_data_collection(collection_name: str) -> bool:
        """Check if collection name represents manual task data"""
        return collection_name == ManualTaskAddress.MANUAL_DATA_COLLECTION

    @staticmethod
    def is_manual_task_address(address: Union[str, CollectionAddress]) -> bool:
        """Check if address represents manual task data"""
        if isinstance(address, str):
            # Handle string format "connection_key:collection_name"
            _, _, collection_part = address.partition(":")
            if not collection_part:
                return False
            return ManualTaskAddress._is_manual_data_collection(collection_part)

        # Handle CollectionAddress object
        return ManualTaskAddress._is_manual_data_collection(address.collection)

    @staticmethod
    def get_connection_key(address: Union[str, CollectionAddress]) -> str:
        """Extract connection config key from manual task address"""
        if not ManualTaskAddress.is_manual_task_address(address):
            raise ValueError(f"Not a manual task address: {address}")

        if isinstance(address, str):
            # Handle string format "connection_key:collection_name"
            return address.split(":")[0]

        # Handle CollectionAddress object
        return address.dataset
