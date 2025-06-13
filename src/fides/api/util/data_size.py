"""
Helpers for estimating the size of large collections of access data.
"""

from __future__ import annotations

import json
import sys
from typing import List, Optional

from loguru import logger

from fides.api.util.collection_util import Row
from fides.api.util.custom_json_encoder import CustomJSONEncoder

# 640MB threshold for external storage
# We only generate an estimated size for large datasets so we want to be conservative
# and fallback to external storage even if we haven't hit the 1GB max limit.
# We also want to pad for encryption and base64 encoding.
LARGE_DATA_THRESHOLD_BYTES = 640 * 1024 * 1024  # 640MB


def calculate_data_size(data: List[Row]) -> int:  # noqa: D401 – utility function
    """Return an approximate JSON-serialized size (in bytes) for a list of *Row*.

    The implementation purposefully avoids serializing the entire payload when
    *data* is large.  For collections >1000 rows we sample a subset, measure the
    encoded size, then extrapolate.  This keeps memory usage bounded while still
    giving us an order-of-magnitude estimate suitable for "should I stream this
    out to S3?" decisions.
    """

    if not data:
        return 0

    try:
        data_count = len(data)

        # For very large datasets, estimate size from a sample to avoid memory issues
        if data_count > 1000:
            logger.debug(
                f"Calculating size for large dataset ({data_count} rows) using sampling"
            )

            sample_size = min(500, max(100, data_count // 20))  # 5 % capped at 500

            # stratified sampling – take items spaced across the set when possible
            if data_count > sample_size * 3:
                step = data_count // sample_size
                sample_indices = list(range(0, data_count, step))[:sample_size]
                sample = [data[i] for i in sample_indices]
            else:
                sample = data[:sample_size]

            sample_json = json.dumps(
                sample, cls=CustomJSONEncoder, separators=(",", ":")
            )
            sample_bytes = len(sample_json.encode("utf-8"))

            avg_record_size = sample_bytes / sample_size
            content_size = int(avg_record_size * data_count)

            # overhead: 2 bytes for [] plus a comma between every record plus 1 % slack
            structure_overhead = 2 + (data_count - 1) + int(content_size * 0.01)
            return content_size + structure_overhead

        # small datasets – just measure
        json_str = json.dumps(data, cls=CustomJSONEncoder, separators=(",", ":"))
        return len(json_str.encode("utf-8"))

    except (TypeError, ValueError) as exc:
        logger.warning(
            f"Failed to calculate JSON size, falling back to sys.getsizeof: {exc}"
        )
        return sys.getsizeof(data)


def is_large_data(
    data: List[Row], threshold_bytes: Optional[int] = None
) -> bool:  # noqa: D401
    """Return *True* if *data* is likely to exceed *threshold_bytes* when serialized."""

    if not data:
        return False

    threshold = (
        threshold_bytes if threshold_bytes is not None else LARGE_DATA_THRESHOLD_BYTES
    )
    size = calculate_data_size(data)
    if size > threshold:
        logger.info(
            f"Data size ({size:,} bytes) exceeds threshold ({threshold:,} bytes) – using external storage"
        )
        return True
    return False


__all__ = [
    "calculate_data_size",
    "is_large_data",
    "LARGE_DATA_THRESHOLD_BYTES",
]
