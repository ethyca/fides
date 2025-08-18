from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from loguru import logger

from fides.api.service.privacy_request.dsr_package.dsr_report_builder import DsrReportBuilder
from fides.api.service.storage.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.schemas import ProcessingMetrics

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def stream_html_dsr_report_to_storage_multipart(
    storage_client: CloudStorageClient,
    bucket_name: str,
    file_key: str,
    data: dict,
    privacy_request: PrivacyRequest
) -> ProcessingMetrics:
    """Stream HTML DSR report to storage multipart upload.

    This function handles the specific logic for generating and streaming DSR reports
    to cloud storage, keeping it separate from generic storage operations.
    """

    # Initiate multipart upload
    response = storage_client.create_multipart_upload(
        bucket_name, file_key, "text/html"
    )
    upload_id = response.upload_id

    parts = []
    part_number = 1

    try:
        # Generate the complete DSR report
        dsr_buffer = DsrReportBuilder(
            privacy_request=privacy_request,
            dsr_data=data,
        ).generate()

        # Split the HTML content into chunks and upload
        html_content = dsr_buffer.getvalue()
        chunk_size = 5 * 1024 * 1024  # 5MB chunks

        for i in range(0, len(html_content), chunk_size):
            chunk = html_content[i:i + chunk_size]
            chunk_buffer = BytesIO(chunk)

            part = storage_client.upload_part(
                bucket_name, upload_id, part_number, chunk_buffer.getvalue()
            )
            parts.append(part)
            part_number += 1

        # Complete multipart upload
        storage_client.complete_multipart_upload(
            bucket_name, file_key, upload_id, parts
        )

        logger.info("Completed HTML DSR report streaming upload with {} parts", len(parts))

        # Return minimal metrics for HTML (no attachments)
        return ProcessingMetrics()

    except Exception as e:
        # Abort multipart upload on failure
        try:
            storage_client.abort_multipart_upload(
                bucket_name, file_key, upload_id
            )
        except Exception as abort_error:
            logger.warning("Failed to abort multipart upload: {}", abort_error)
        raise e
