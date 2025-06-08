import json
import sys
from typing import List, Optional

from loguru import logger

from fides.api.util.collection_util import Row
from fides.api.util.custom_json_encoder import CustomJSONEncoder

# 1GB threshold for external storage
LARGE_DATA_THRESHOLD_BYTES = 1024 * 1024 * 1024  # 1GB


def calculate_data_size(data: List[Row]) -> int:
    """Calculate the approximate serialized size of access data in bytes using a memory-efficient approach"""
    if not data:
        return 0

    try:
        data_count = len(data)

        # For very large datasets, estimate size from a sample to avoid memory issues
        if data_count > 1000:  # For large datasets, use sampling
            logger.debug(
                f"Calculating size for large dataset ({data_count} rows) using sampling"
            )
            # Take a representative sample
            sample_size = min(100, data_count)
            sample = data[:sample_size]

            # Calculate sample size
            sample_json = json.dumps(
                sample, cls=CustomJSONEncoder, separators=(",", ":")
            )
            sample_bytes = len(sample_json.encode("utf-8"))

            # Estimate total size (with some overhead for JSON structure)
            estimated_size = (sample_bytes * data_count) // sample_size
            # Add overhead for JSON array brackets and commas
            estimated_size += data_count * 2  # Rough estimate for commas and spacing

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
