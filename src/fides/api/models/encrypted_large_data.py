import json
import sys
from datetime import datetime
from typing import Any, List, Optional, Type

from loguru import logger

from fides.api.api.deps import get_autoclose_db_session
from fides.api.schemas.external_storage import ExternalStorageMetadata
from fides.api.service.external_data_storage import (
    ExternalDataStorageError,
    ExternalDataStorageService,
)
from fides.api.util.collection_util import Row
from fides.api.util.custom_json_encoder import CustomJSONEncoder

# 640MB threshold for external storage
# We only generate an estimated size for large datasets so we want to be conservative
# and fallback to external storage even if we haven't hit the 1GB max limit.
# We also want to pad for encryption and base64 encoding.
LARGE_DATA_THRESHOLD_BYTES = 640 * 1024 * 1024  # 640MB


def calculate_data_size(data: List[Row]) -> int:
    """Calculate the approximate serialized size of access data in bytes using a memory-efficient approach

    We need to determine the size of data in a memory-efficient way. Calling `sys.getsizeof` is not accurate for
    `Dict` and the way to calculate exact size could take up a lot of memory (`json.dumps`). I went with a
    sampling approach where we only need to call `json.dumps` on a sample of data. We know the most
    likely reason for large data is a large number of rows vs. a row with a lot of data.

    We use this knowledge to:

    - Take a sample of records from the list of data
    - Calculate exact size of the samples
    - Extrapolate the estimated size based on the total number of records
    """

    if not data:
        return 0

    try:
        data_count = len(data)

        # For very large datasets, estimate size from a sample to avoid memory issues
        if data_count > 1000:  # For large datasets, use sampling
            logger.debug(
                f"Calculating size for large dataset ({data_count} rows) using sampling"
            )

            # Use larger sample size for better accuracy (up to 500 records)
            sample_size = min(
                500, max(100, data_count // 20)
            )  # At least 100, up to 500, or 5% of data

            # Use stratified sampling for better representation
            if data_count > sample_size * 3:
                # Take samples from beginning, middle, and end
                step = data_count // sample_size
                sample_indices = list(range(0, data_count, step))[:sample_size]
                sample = [data[i] for i in sample_indices]
            else:
                # For smaller datasets, just take from the beginning
                sample = data[:sample_size]

            # Calculate sample size
            sample_json = json.dumps(
                sample, cls=CustomJSONEncoder, separators=(",", ":")
            )
            sample_bytes = len(sample_json.encode("utf-8"))

            # Better estimation accounting for JSON structure overhead
            # Calculate per-record average
            avg_record_size = sample_bytes / sample_size

            # Estimate content size
            content_size = int(avg_record_size * data_count)

            # Add more accurate JSON structure overhead
            # - Array brackets: 2 bytes
            # - Commas between records: (data_count - 1) bytes
            # - Some padding for variations: 1% of content size
            structure_overhead = 2 + (data_count - 1) + int(content_size * 0.01)

            estimated_size = content_size + structure_overhead

            logger.debug(f"Sample: {sample_size} records, {sample_bytes} bytes")
            logger.debug(f"Avg per record: {avg_record_size:.1f} bytes")
            logger.debug(
                f"Estimated size: {estimated_size:,} bytes ({estimated_size / (1024*1024*1024):.2f} GB)"
            )
            return estimated_size

        # For smaller datasets, calculate exact size
        json_str = json.dumps(data, cls=CustomJSONEncoder, separators=(",", ":"))
        size = len(json_str.encode("utf-8"))
        return size

    except (TypeError, ValueError) as e:
        logger.warning(
            f"Failed to calculate JSON size, falling back to sys.getsizeof: {e}"
        )
        # Fallback to sys.getsizeof if JSON serialization fails
        return sys.getsizeof(data)


def is_large_data(data: List[Row], threshold_bytes: Optional[int] = None) -> bool:
    """Check if data exceeds the large data threshold

    Args:
        data: The data to check
        threshold_bytes: Custom threshold in bytes. If None, uses LARGE_DATA_THRESHOLD_BYTES
    """
    if not data:
        return False

    threshold = (
        threshold_bytes if threshold_bytes is not None else LARGE_DATA_THRESHOLD_BYTES
    )
    size = calculate_data_size(data)
    is_large = size > threshold

    if is_large:
        logger.info(
            f"Data size ({size:,} bytes) exceeds threshold ({threshold:,} bytes) - using external storage"
        )

    return is_large


class EncryptedLargeDataDescriptor:
    """
    A Python descriptor for database fields with encrypted external storage fallback.

    This implements Python's descriptor protocol (by defining __get__ and __set__ methods)
    to intercept attribute access and provide custom behavior. When you declare:

    ```python
    class RequestTask(Base):
        access_data = EncryptedLargeDataDescriptor("access_data")
    ```

    The descriptor automatically:
    1. Encrypts data using SQLAlchemy-Utils StringEncryptedType
    2. Uses external storage (S3, GCS, local) when data exceeds size thresholds
    3. Handles cleanup of external storage files when data changes
    4. Works transparently - fields behave like normal Python attributes

    Storage paths use the format: {model_name}/{instance_id}/{field_name}/{timestamp}

    This pattern eliminates duplicate code across multiple encrypted fields while providing
    a clean, reusable interface that works with any SQLAlchemy model with an 'id' attribute.
    """

    def __init__(
        self,
        field_name: str,
        empty_default: Optional[Any] = None,
        threshold_bytes: Optional[int] = None,
    ):
        """
        Initialize the descriptor.

        Args:
            field_name: The name of the database column (e.g., "access_data")
            empty_default: Default value when data is None/empty ([] for lists, {} for dicts)
            threshold_bytes: Optional custom threshold for external storage
        """
        self.field_name = field_name
        self.private_field = f"_{field_name}"
        self.empty_default = empty_default if empty_default is not None else []
        self.threshold_bytes = threshold_bytes or LARGE_DATA_THRESHOLD_BYTES
        self.model_class: Optional[str] = None
        self.name: Optional[str] = None

    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self.name = name
        self.model_class = owner.__name__

    def _generate_storage_path(self, instance: Any) -> str:
        """
        Generate a storage path using generic naming.

        Format: {model_type}/{instance_id}/{field_name}/{timestamp}
        """
        instance_id = getattr(instance, "id", None)
        if not instance_id:
            raise ValueError(f"Instance {instance} must have an 'id' attribute")

        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")

        return f"{self.model_class}/{instance_id}/{self.field_name}/{timestamp}.txt"

    def __get__(self, instance: Any, owner: Type) -> Any:
        """
        Get the value, handling external storage retrieval if needed.
        """
        if instance is None:
            return self

        # Get the raw data from the private field
        raw_data = getattr(instance, self.private_field)
        if raw_data is None:
            return None

        # Check if it's external storage metadata
        if isinstance(raw_data, dict) and "storage_type" in raw_data:
            logger.info(
                f"Reading {self.model_class}.{self.field_name} from external storage "
                f"({raw_data.get('storage_type')})"
            )
            try:
                metadata = ExternalStorageMetadata.model_validate(raw_data)
                data = self._retrieve_external_data(metadata)

                # Log retrieval details
                record_count = len(data) if isinstance(data, list) else "N/A"
                logger.info(
                    f"Successfully retrieved {self.model_class}.{self.field_name} "
                    f"from external storage (records: {record_count})"
                )
                return data if data is not None else self.empty_default
            except Exception as e:
                logger.error(
                    f"Failed to retrieve {self.model_class}.{self.field_name} "
                    f"from external storage: {str(e)}"
                )
                raise ExternalDataStorageError(
                    f"Failed to retrieve {self.field_name}: {str(e)}"
                ) from e
        else:
            return raw_data

    def __set__(self, instance: Any, value: Any) -> None:
        """
        Set the value, automatically using external storage for large data.
        """
        if not value:
            # Clean up any existing external storage
            self._cleanup_external_data(instance)
            # Set to empty default
            setattr(instance, self.private_field, self.empty_default)
            return

        # Check if the data is the same as what's already stored
        try:
            current_data = self.__get__(instance, type(instance))
            if current_data == value:
                # Data is identical, no need to update
                return
        except Exception:
            # If we can't get current data, proceed with update
            pass

        # Calculate data size
        data_size = calculate_data_size(value)

        # Check if data exceeds threshold
        if data_size > self.threshold_bytes:
            logger.info(
                f"{self.model_class}.{self.field_name}: Data size ({data_size:,} bytes) "
                f"exceeds threshold ({self.threshold_bytes:,} bytes), storing externally"
            )
            # Clean up any existing external storage first
            self._cleanup_external_data(instance)

            # Store in external storage
            metadata = self._store_external_data(instance, value)
            setattr(instance, self.private_field, metadata.model_dump())
        else:
            # Clean up any existing external storage
            self._cleanup_external_data(instance)
            # Store directly in database
            setattr(instance, self.private_field, value)

    def _store_external_data(self, instance: Any, data: Any) -> ExternalStorageMetadata:
        """
        Store data in external storage using generic path structure.
        """
        storage_path = self._generate_storage_path(instance)

        with get_autoclose_db_session() as session:
            metadata = ExternalDataStorageService.store_data(
                db=session,
                storage_path=storage_path,
                data=data,
            )

            logger.info(
                f"Stored {self.model_class}.{self.field_name} to external storage: {storage_path}"
            )

            return metadata

    def _retrieve_external_data(self, metadata: ExternalStorageMetadata) -> Any:
        """
        Retrieve data from external storage.
        """
        with get_autoclose_db_session() as session:
            return ExternalDataStorageService.retrieve_data(
                db=session,
                metadata=metadata,
            )

    def _cleanup_external_data(self, instance: Any) -> None:
        """Clean up external storage if it exists."""
        raw_data = getattr(instance, self.private_field, None)
        if isinstance(raw_data, dict) and "storage_type" in raw_data:
            try:
                metadata = ExternalStorageMetadata.model_validate(raw_data)
                with get_autoclose_db_session() as session:
                    ExternalDataStorageService.delete_data(
                        db=session,
                        metadata=metadata,
                    )

                logger.info(
                    f"Cleaned up external storage for {self.model_class}.{self.field_name}: "
                    f"{metadata.file_key}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup external {self.field_name}: {str(e)}"
                )

    def cleanup(self, instance: Any) -> None:
        """Public method to cleanup external storage."""
        self._cleanup_external_data(instance)
