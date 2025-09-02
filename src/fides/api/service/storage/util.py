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


def get_unique_filename(filename: str, used_filenames: set[str]) -> str:
    """
    Generates a unique filename by appending a counter if the file already exists.
    Tracks filenames per dataset to match DSR report builder behavior.

    Args:
        filename: The original filename
        used_filenames: Set of filenames that have already been used

    Returns:
        A unique filename that won't conflict with existing files in the same dataset
    """
    # Initialize the used filenames set for this dataset if it doesn't exist

    base_name, extension = os.path.splitext(filename)
    counter = 1
    unique_filename = filename

    # Check if file exists in this dataset's used_filenames set
    while unique_filename in used_filenames:
        unique_filename = f"{base_name}_{counter}{extension}"
        counter += 1

    return unique_filename
