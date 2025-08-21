from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def stream_html_dsr_report_to_storage_multipart(
    storage_client: SmartOpenStorageClient,
    bucket_name: str,
    file_key: str,
    data: dict,
    privacy_request: PrivacyRequest,
) -> None:
    """Stream HTML DSR report to storage using smart-open streaming.

    This function now uses smart-open's efficient streaming capabilities for uploading
    DSR reports to cloud storage, eliminating the need for complex multipart logic.
    """

    # Generate the complete DSR report
    dsr_buffer = DsrReportBuilder(
        privacy_request=privacy_request,
        dsr_data=data,
    ).generate()

    # Get the HTML content
    html_content = dsr_buffer.getvalue()
    content_size = len(html_content)

    logger.info(
        "DSR report size {} bytes, using smart-open streaming upload",
        content_size,
    )

    try:
        # Use smart-open's streaming upload for efficient memory usage
        with storage_client.stream_upload(
            bucket_name, file_key, content_type="text/html"
        ) as upload_stream:
            upload_stream.write(html_content)

        logger.info(
            "Successfully uploaded DSR report using smart-open streaming: {}", file_key
        )

    except Exception as e:
        logger.error("Failed to upload DSR report using smart-open streaming: {}", e)
        raise e
