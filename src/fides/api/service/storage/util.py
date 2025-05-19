import os
from enum import Enum as EnumType

from loguru import logger


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

# Default to 10MB if not specified in environment
LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10 MB threshold


def get_local_filename(file_key: str) -> str:
    """Verifies that the local storage directory exists and returns the local filepath"""
    if not os.path.exists(LOCAL_FIDES_UPLOAD_DIRECTORY):
        os.makedirs(LOCAL_FIDES_UPLOAD_DIRECTORY)
    return f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{file_key}"


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
