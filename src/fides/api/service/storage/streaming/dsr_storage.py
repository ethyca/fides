from __future__ import annotations

import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any, Generator, Tuple

from loguru import logger
from stream_zip import _ZIP_32_TYPE

from fides.api.service.storage.streaming.schemas import AttachmentProcessingInfo
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient


def stream_dsr_buffer_to_storage(
    storage_client: SmartOpenStorageClient,
    bucket_name: str,
    file_key: str,
    dsr_buffer: BytesIO,
    content_type: str = "application/zip",
) -> None:
    """Stream DSR buffer to storage using smart-open streaming.

    This function handles only the storage streaming concern, accepting a pre-generated
    DSR buffer to maintain clear separation of concerns.

    Args:
        storage_client: The storage client for streaming uploads
        bucket_name: Storage bucket name
        file_key: File key in storage
        dsr_buffer: Pre-generated DSR report buffer (BytesIO)
        content_type: MIME type for the uploaded file (defaults to application/zip)
    """
    # Get the content from the buffer
    content = dsr_buffer.getvalue()
    try:
        # Use smart-open's streaming upload for efficient memory usage
        with storage_client.stream_upload(
            bucket_name, file_key, content_type=content_type
        ) as upload_stream:
            upload_stream.write(content)

    except Exception as e:
        logger.error("Failed to upload DSR report using smart-open streaming: {}", e)
        raise e


def create_dsr_report_files_generator(
    dsr_buffer: BytesIO,
    all_attachments: list["AttachmentProcessingInfo"],
    bucket_name: str,
    max_workers: int,
    batch_size: int,
) -> Generator[
    Tuple[str, datetime, int, Any, Generator[bytes, None, None]], None, None
]:
    """Create a ZIP generator for DSR report HTML files only.

    This method extracts and yields the HTML files from a DSR report buffer.
    Note: This function only handles the DSR report files (HTML, CSS, etc.).
    The caller is responsible for combining this with attachment files to create
    the complete ZIP.

    Args:
        dsr_buffer: The DSR report buffer (ZIP file as BytesIO)
        all_attachments: List of validated attachments (used for logging only)
        bucket_name: Storage bucket name (used for logging only)
        max_workers: Maximum parallel workers (used for logging only)
        batch_size: Number of attachments to process in each batch (used for logging only)

    Returns:
        Generator yielding DSR report files in stream_zip format
    """
    logger.debug(
        f"Creating DSR report files generator with {len(all_attachments)} attachments"
    )

    # Reset buffer position to ensure we can read from it
    dsr_buffer.seek(0)

    # Extract and yield the DSR report files from the buffer
    # The dsr_buffer is already a ZIP file, so we need to extract and re-yield its contents
    with zipfile.ZipFile(dsr_buffer) as dsr_zip:
        for file_info in dsr_zip.filelist:
            if not file_info.is_dir():
                # Read the file content and yield it in stream_zip format
                content = dsr_zip.read(file_info.filename)

                def content_generator(
                    file_content: bytes,
                ) -> Generator[bytes, None, None]:
                    yield file_content

                yield file_info.filename, datetime.now(), 0o644, _ZIP_32_TYPE(), content_generator(
                    content
                )

    logger.debug("DSR report files extracted and ready for ZIP creation")
