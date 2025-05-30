import time as time_module
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

from loguru import logger

from fides.api.models.attachment import Attachment, AttachmentType
from fides.api.schemas.storage.storage import ResponseFormat


@dataclass
class AttachmentData:
    """Data structure for attachment metadata and content.
    Using a dataclass rather than a Pydantic model here for the following reasons:
    - The data structure is simple and doesn't need complex validation.
    - The fields being used have already been validated and are properly typed.
    - The class is used internally for data transfer, not for API serialization.
    - Performance is important since this is used in a data processing pipeline.
    """

    file_name: str
    file_size: Optional[int]
    download_url: Optional[str]
    content_type: str
    fileobj: Optional[Any] = None

    def to_upload_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for upload, including fileobj."""
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "download_url": self.download_url,
            "content_type": self.content_type,
            "fileobj": self.fileobj,
        }

    def to_storage_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage, excluding fileobj."""
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "download_url": self.download_url,
            "content_type": self.content_type,
        }


def get_attachments_content(
    loaded_attachments: List[Attachment],
) -> Iterator[AttachmentData]:
    """
    Retrieves all attachments associated with a privacy request that are marked to be included with the access package.
    Yields AttachmentData objects containing attachment metadata and content.
    Uses generators to minimize memory usage.

    Args:
        loaded_attachments: List of Attachment objects to process

    Yields:
        AttachmentData object containing attachment metadata and content
    """
    start_time = time_module.time()
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_size = 0

    for attachment in loaded_attachments:
        if attachment.attachment_type != AttachmentType.include_with_access_package:
            skipped_count += 1
            continue

        try:
            # Get size and download URL using retrieve_attachment
            size, url = attachment.retrieve_attachment()
            total_size += size if size else 0

            # If config response format is html, we need to get the fileobj
            fileobj = None
            if attachment.config.format.value == ResponseFormat.html.value:  # type: ignore[attr-defined]
                _, fileobj = attachment.retrieve_attachment_content()
                if not fileobj:
                    logger.warning(
                        "No content retrieved for attachment {}", attachment.file_name
                    )
                    skipped_count += 1
                    continue

            processed_count += 1
            yield AttachmentData(
                file_name=attachment.file_name,
                file_size=size,
                download_url=str(url) if url else None,
                content_type=attachment.content_type,
                fileobj=fileobj,
            )

        except Exception as e:
            error_count += 1
            logger.error(
                "Error processing attachment {}: {}", attachment.file_name, str(e)
            )
            continue

    # Log final metrics
    time_taken = time_module.time() - start_time
    logger.bind(
        time_to_process=time_taken,
        total_attachments=len(loaded_attachments),
        processed_attachments=processed_count,
        skipped_attachments=skipped_count,
        error_attachments=error_count,
        total_size_bytes=total_size,
    ).info("Attachment processing complete")


def process_attachments_for_upload(
    attachments: Iterator[AttachmentData],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process attachments into separate upload and storage formats.
    Returns both formats to avoid processing attachments twice.
    """
    upload_attachments = []
    storage_attachments = []

    for attachment in attachments:
        upload_attachments.append(attachment.to_upload_dict())
        storage_attachments.append(attachment.to_storage_dict())

    return upload_attachments, storage_attachments
