import os
from enum import Enum as EnumType

from loguru import logger

# This is the max file size for downloading the content of an attachment.
# This is an industry standard used by companies like Google and Microsoft.
LARGE_FILE_THRESHOLD = 25 * 1024 * 1024  # 25 MB


class AllowedFileType(EnumType):
    """
    A class that contains the allowed file types and their MIME types.
    """

    pdf = "application/pdf"
    doc = "application/msword"
    docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    txt = "text/plain"
    jpg = "image/jpeg"
    jpeg = "image/jpeg"
    png = "image/png"
    xls = "application/vnd.ms-excel"
    xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    csv = "text/csv"
    zip = "application/zip"


LOCAL_FIDES_UPLOAD_DIRECTORY = "fides_uploads"


def get_local_filename(file_key: str) -> str:
    """Verifies that the local storage directory exists and returns the local filepath.

    This extra security checks are to prevent directory traversal attacks and "complete business and technical destruction".
    Thanks Claude.

    Args:
        file_key: The key/path for the file

    Returns:
        The full local filepath

    Raises:
        ValueError: If the file_key is invalid or would result in a path outside the upload directory
    """
    # Basic validation
    if not file_key:
        raise ValueError("File key cannot be empty")

    # Security checks before normalization
    if file_key.startswith("/"):
        raise ValueError("Invalid file key: cannot start with '/'")

    # Normalize the path to handle any path separators consistently
    # First normalize using os.path.normpath to handle any redundant separators
    normalized_key = os.path.normpath(file_key)
    # Then convert all separators to forward slashes for consistency
    normalized_key = normalized_key.replace("\\", "/")

    # Additional security: ensure the final path is within the upload directory
    final_path = os.path.join(LOCAL_FIDES_UPLOAD_DIRECTORY, normalized_key)
    if not os.path.abspath(final_path).startswith(
        os.path.abspath(LOCAL_FIDES_UPLOAD_DIRECTORY)
    ):
        raise ValueError(
            "Invalid file key: would result in path outside upload directory"
        )

    # Create all necessary directories
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    return final_path


def get_allowed_file_type_or_raise(file_key: str) -> str:
    """Verifies that the file type is allowed and returns the MIME type"""
    error_msg = f"Invalid or unallowed file extension: {file_key}"
    if "." not in file_key:
        logger.warning(f"File key {file_key} does not have a file extension")
        raise ValueError(error_msg)
    file_type = file_key.split(".")[-1]
    try:
        return AllowedFileType[file_type].value
    except KeyError:
        raise ValueError(error_msg)



def adaptive_chunk_size(file_size: int) -> int:
    """Determine optimal chunk size based on file size.

    Larger files use larger chunks for better performance.
    """
    if file_size > 100 * 1024 * 1024:  # 100MB+
        return 1024 * 1024  # 1MB chunks
    elif file_size > 10 * 1024 * 1024:  # 10MB+
        return 256 * 1024   # 256KB chunks
    elif file_size > 1 * 1024 * 1024:   # 1MB+
        return 128 * 1024   # 128KB chunks
    else:
        return 64 * 1024    # 64KB chunks


def should_split_package(data: dict, max_attachments: int = 100, max_total_size_gb: int = 5) -> bool:
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
                estimated_total_size += sum(att.get("size", 1024 * 1024) for att in attachments)

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

    return (total_attachments > max_attachments or
            estimated_total_size > max_total_size_gb * 1024 * 1024 * 1024)
