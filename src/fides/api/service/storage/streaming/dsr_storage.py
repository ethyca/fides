from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from loguru import logger

from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.util import (
    AWS_MIN_PART_SIZE,
    CHUNK_SIZE_THRESHOLD,
)

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def stream_html_dsr_report_to_storage_multipart(
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    data: dict,
    privacy_request: PrivacyRequest,
) -> None:
    """Stream HTML DSR report to storage with intelligent upload strategy.

    This function handles the specific logic for generating and streaming DSR reports
    to cloud storage. It automatically chooses between single upload and multipart upload
    based on file size to optimize performance and avoid AWS S3 part size validation errors.

    For small files (< 5MB), it uses single upload. For large files (>= 5MB), it uses
    multipart upload with proper chunk sizing.
    """

    # Generate the complete DSR report
    dsr_buffer = DsrReportBuilder(
        privacy_request=privacy_request,
        dsr_data=data,
    ).generate()

    # Get the HTML content and check its size
    html_content = dsr_buffer.getvalue()
    content_size = len(html_content)

    # For small files, use single upload to avoid AWS S3 part size validation errors
    if content_size < AWS_MIN_PART_SIZE:
        logger.info(
            "DSR report size {} bytes is below multipart threshold ({} bytes), using single upload",
            content_size,
            AWS_MIN_PART_SIZE,
        )

        try:
            storage_client.put_object(
                bucket_name,
                file_key,
                html_content,
                content_type="text/html",
            )
            logger.info(
                "Successfully uploaded DSR report using single upload: {}", file_key
            )
        except Exception as e:
            logger.error("Failed to upload DSR report using single upload: {}", e)
            raise e
        return

    # For large files, use multipart upload with proper chunk sizing
    logger.info(
        "DSR report size {} bytes is above multipart threshold ({} bytes), using multipart upload",
        content_size,
        AWS_MIN_PART_SIZE,
    )

    # Initiate multipart upload
    response = storage_client.create_multipart_upload(
        bucket_name, file_key, "text/html"
    )
    upload_id = response.upload_id

    parts = []
    part_number = 1

    try:
        # Split the HTML content into chunks that meet AWS S3 minimum part size requirements
        chunk_size = max(CHUNK_SIZE_THRESHOLD, AWS_MIN_PART_SIZE)

        for i in range(0, content_size, chunk_size):
            chunk = html_content[i : i + chunk_size]

            # Ensure the last part meets minimum size requirements (AWS allows last part to be smaller)
            if i + chunk_size >= content_size:
                # This is the last part, it can be smaller than the minimum
                pass
            elif len(chunk) < AWS_MIN_PART_SIZE:
                # This is not the last part but it's too small, extend it to meet minimum
                next_chunk_start = i + chunk_size
                if next_chunk_start < content_size:
                    # Extend this chunk to include part of the next chunk
                    extended_size = min(AWS_MIN_PART_SIZE, content_size - i)
                    chunk = html_content[i : i + extended_size]
                    # Adjust the next iteration to account for the overlap
                    i = i + extended_size - chunk_size

            part = storage_client.upload_part(
                bucket_name, file_key, upload_id, part_number, chunk
            )
            parts.append(part)
            part_number += 1

        # Complete multipart upload
        storage_client.complete_multipart_upload(
            bucket_name, file_key, upload_id, parts
        )

        logger.info(
            "Completed HTML DSR report multipart upload with {} parts", len(parts)
        )

    except Exception as e:
        # Abort multipart upload on failure
        try:
            storage_client.abort_multipart_upload(bucket_name, file_key, upload_id)
        except Exception as abort_error:
            logger.warning("Failed to abort multipart upload: {}", abort_error)
        raise e
