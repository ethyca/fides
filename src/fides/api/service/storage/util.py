import os
from typing import Optional

from loguru import logger

ALLOWED_FILE_TYPES = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "zip": "application/zip",
}

LOCAL_FIDES_UPLOAD_DIRECTORY = "fides_uploads"

# Default to 5MB if not specified in environment
DEFAULT_LARGE_FILE_THRESHOLD = 5 * 1024 * 1024  # 5 MB threshold
# This checks to see if the environment variable is set and if it is, it uses that value
# Otherwise, it uses the default value
LARGE_FILE_THRESHOLD = int(
    os.getenv("FIDES__LARGE_FILE_THRESHOLD", str(DEFAULT_LARGE_FILE_THRESHOLD))
)


def get_local_filename(file_key: str) -> str:
    """Verifies that the local storage directory exists"""
    if not os.path.exists(LOCAL_FIDES_UPLOAD_DIRECTORY):
        os.makedirs(LOCAL_FIDES_UPLOAD_DIRECTORY)
    return f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{file_key}"


def get_file_type(file_key: str) -> Optional[str]:
    """Returns the file type of the file"""
    if "." not in file_key:
        logger.warning(f"File key {file_key} does not have a file extension")
        return None
    file_type = file_key.split(".")[-1]
    if file_type not in ALLOWED_FILE_TYPES:
        raise ValueError(f"File type {file_type} is not allowed")
    return file_type
