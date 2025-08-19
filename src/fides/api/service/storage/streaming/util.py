# AWS S3 multipart upload requirements
AWS_MIN_PART_SIZE = 5 * 1024 * 1024  # 5MB minimum per part (except last)
AWS_MAX_PART_SIZE = 5 * 1024 * 1024 * 1024  # 5GB maximum per part
AWS_MAX_PARTS = 10000  # Maximum number of parts per multipart upload

# GCS resumable upload requirements
GCS_MIN_CHUNK_SIZE = 256 * 1024  # 256KB minimum chunk size for resumable uploads
GCS_MAX_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB recommended maximum chunk size
GCS_MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024 * 1024  # 5TB maximum file size
GCS_MAX_RESUMABLE_SESSIONS = (
    1000  # Maximum concurrent resumable upload sessions per bucket
)

# Performance and memory thresholds
ZIP_BUFFER_THRESHOLD = 5 * 1024 * 1024  # 5MB threshold for zip buffer uploads
CHUNK_SIZE_THRESHOLD = 5 * 1024 * 1024  # 5MB threshold for chunk-based uploads

# File size thresholds for different operations
LARGE_FILE_THRESHOLD = 25 * 1024 * 1024  # 25MB threshold for large file handling

# Error messages
ENTITY_TOO_SMALL_ERROR = "EntityTooSmall"
MIN_PART_SIZE_ERROR_MSG = (
    f"Part size below AWS S3 minimum requirement ({AWS_MIN_PART_SIZE // (1024*1024)}MB)"
)
GCS_CHUNK_SIZE_ERROR_MSG = (
    f"Chunk size below GCS minimum requirement ({GCS_MIN_CHUNK_SIZE // 1024}KB)"
)


def adaptive_chunk_size(file_size: int) -> int:
    """Determine optimal chunk size based on file size.

    Larger files use larger chunks for better performance.
    """
    if file_size > 100 * 1024 * 1024:  # 100MB+
        return 1024 * 1024  # 1MB chunks
    elif file_size > 10 * 1024 * 1024:  # 10MB+
        return 256 * 1024  # 256KB chunks
    elif file_size > 1 * 1024 * 1024:  # 1MB+
        return 128 * 1024  # 128KB chunks
    else:
        return 64 * 1024  # 64KB chunks


def should_split_package(
    data: dict, max_attachments: int = 100, max_total_size_gb: int = 5
) -> bool:
    """Determine if the dataset should be split into multiple packages.

    Args:
        data: The data to process
        max_attachments: Maximum attachments per package
        max_total_size_gb: Maximum total size in GB per package

    Returns:
        True if package should be split
    """

    def count_attachments_recursive(obj):
        """Recursively count attachments and calculate total size."""
        total_attachments = 0
        estimated_total_size = 0

        if isinstance(obj, dict):
            # Check if this dict has attachments
            if "attachments" in obj:
                attachments = obj["attachments"]
                total_attachments += len(attachments)
                estimated_total_size += sum(
                    att.get("size", 1024 * 1024) for att in attachments
                )

            # Recursively check all values in the dict
            for value in obj.values():
                sub_attachments, sub_size = count_attachments_recursive(value)
                total_attachments += sub_attachments
                estimated_total_size += sub_size

        elif isinstance(obj, list):
            # Recursively check all items in the list
            for item in obj:
                sub_attachments, sub_size = count_attachments_recursive(item)
                total_attachments += sub_attachments
                estimated_total_size += sub_size

        return total_attachments, estimated_total_size

    total_attachments, estimated_total_size = count_attachments_recursive(data)

    return (
        total_attachments > max_attachments
        or estimated_total_size > max_total_size_gb * 1024 * 1024 * 1024
    )
