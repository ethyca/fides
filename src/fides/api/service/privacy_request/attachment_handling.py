import time as time_module
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

from loguru import logger

from fides.api.models.attachment import Attachment, AttachmentType
from fides.api.schemas.storage.storage import StorageDetails, StorageType


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
    bucket_name: str
    file_key: str
    storage_key: str

    def to_upload_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for upload, including presigned URL."""
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "download_url": self.download_url,
            "content_type": self.content_type,
        }

    def to_storage_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage, including the elements needed to recreated the presigned URL."""
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "bucket_name": self.bucket_name,
            "file_key": self.file_key,
            "storage_key": self.storage_key,
        }


def get_attachments_content(
    loaded_attachments: List[Attachment],
) -> Iterator[AttachmentData]:
    """
    Retrieves all attachments associated with a privacy request that are marked to be included with the access package.
    Yields AttachmentData objects containing attachment metadata and download urls.
    Uses generators to minimize memory usage.

    Args:
        loaded_attachments: List of Attachment objects to process

    Yields:
        AttachmentData object containing attachment metadata and url
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
            if url is None:
                logger.warning(
                    "No download URL retrieved for attachment {}", attachment.file_name
                )
                skipped_count += 1
                continue

            processed_count += 1

            # Handle bucket_name differently for different storage types
            bucket_name = None
            if attachment.config.type in [StorageType.s3, StorageType.gcs]:
                bucket_name = attachment.config.details[StorageDetails.BUCKET.value]
            # For local storage, bucket_name is not needed

            yield AttachmentData(
                file_name=attachment.file_name,
                file_size=size,
                download_url=str(url) if url else None,
                content_type=attachment.content_type,
                bucket_name=bucket_name or "",  # Empty string for local storage
                file_key=attachment.file_key,
                storage_key=attachment.storage_key,
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
    Returns both formats:
    - upload_attachments: Used for uploading to access packages
    - storage_attachments: Used for saving filtered access results
    """
    upload_attachments = []
    storage_attachments = []

    for attachment in attachments:
        storage_attachments.append(attachment.to_storage_dict())
        upload_attachments.append(attachment.to_upload_dict())

    return upload_attachments, storage_attachments
