from typing import Optional
from zipfile import ZipFile

from defusedxml.ElementTree import fromstring

from fides.api.common_exceptions import ValidationError

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB
CHUNK_SIZE = 1024


def verify_svg(contents: str) -> None:
    """
    Verifies the provided SVG content.

    This function checks the given SVG content string for potential issues and throws an exception if any are found.
    It first attempts to parse the SVG content using 'defusedxml.fromstring'. If the parsing is unsuccessful, this
    will raise an exception, indicating that the SVG content may contain unsafe XML.

    :param contents: The SVG content as a string.
    :raises ValidationError: If the SVG content contains unsafe XML or 'use xlink'
    """
    try:
        fromstring(contents)
    except Exception:
        raise ValidationError("SVG file contains unsafe XML.")

    if "use xlink" in contents:
        raise ValidationError("SVG files with xlink references are not allowed.")


def verify_zip(zip_file: ZipFile, max_file_size: Optional[int] = None) -> None:
    """
    Function to safely verify the contents of zipped files. It prevents potential
    'zip bomb' attacks by checking the file size of the files in the zip without fully
    extracting them. If the size of any file in the zip exceeds the specified
    max_file_size, it raises a ValueError. If the max_file_size is not provided,
    it uses a default value of 16 MB.

    :param zip_file: A ZipFile object to be verified.
    :param max_file_size: An optional integer specifying the maximum bytes allowed per file. If not provided, a default value is used.
    :raises ValueError: If a file in the zip file exceeds the maximum allowed size
    """

    if max_file_size is None:
        max_file_size = MAX_FILE_SIZE

    for file_info in zip_file.infolist():
        file_size = 0

        with zip_file.open(file_info) as file:
            # wraps the file read in an iterator that stops once no bytes
            # are returned or the max file size is reached
            for chunk in iter(lambda f=file: f.read(CHUNK_SIZE), b""):  # type: ignore
                file_size += len(chunk)

                if file_size > max_file_size:
                    raise ValueError("File size exceeds maximum allowed size")
