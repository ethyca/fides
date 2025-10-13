"""Handler for storing and managing attachments from async polling operations."""

from io import BytesIO
from typing import List, Union

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.models.storage import get_active_default_storage_config
from fides.api.util.collection_util import Row


class PollingAttachmentHandler:
    """Utility class for handling attachment storage and metadata in polling operations."""

    @staticmethod
    def store_attachment(
        session: Session,
        request_task: RequestTask,
        attachment_data: bytes,
        filename: str,
    ) -> str:
        """
        Store polling attachment data and return attachment ID.

        This utility function handles the storage of attachment data
        from polling results and creates the necessary database records.

        Args:
            session: Database session
            request_task: The request task associated with this attachment
            attachment_data: The binary attachment data to store
            filename: The filename for the attachment

        Returns:
            str: The ID of the created attachment

        Raises:
            PrivacyRequestError: If storage configuration is not found or storage fails
        """
        try:
            # Get active storage config
            storage_config = get_active_default_storage_config(session)
            if not storage_config:
                raise PrivacyRequestError("No active storage configuration found")

            # Create attachment record and upload to storage
            attachment = Attachment.create_and_upload(
                db=session,
                data={
                    "file_name": filename,
                    "attachment_type": AttachmentType.include_with_access_package,
                    "storage_key": storage_config.key,
                },
                attachment_file=BytesIO(attachment_data),
            )

            # Create attachment references
            AttachmentReference.create(
                db=session,
                data={
                    "attachment_id": attachment.id,
                    "reference_id": request_task.id,
                    "reference_type": AttachmentReferenceType.request_task,
                },
            )

            AttachmentReference.create(
                db=session,
                data={
                    "attachment_id": attachment.id,
                    "reference_id": request_task.privacy_request.id,
                    "reference_type": AttachmentReferenceType.privacy_request,
                },
            )

            logger.info(
                f"Successfully stored polling attachment {attachment.id} for request_task {request_task.id}"
            )
            return attachment.id

        except Exception as e:
            logger.error(f"Failed to store polling attachment: {e}")
            raise PrivacyRequestError(f"Failed to store polling attachment: {e}")

    @staticmethod
    def ensure_attachment_bytes(data: Union[List[Row], bytes]) -> bytes:
        """
        Ensure attachment polling results provide bytes content.

        Args:
            data: The data that should be bytes

        Returns:
            bytes: The validated bytes data

        Raises:
            PrivacyRequestError: If data is not bytes
        """
        if isinstance(data, bytes):
            return data
        raise PrivacyRequestError("Expected bytes data for attachment polling result")

    @staticmethod
    def add_metadata_to_rows(db: Session, attachment_id: str, rows: List[Row]) -> None:
        """
        Add attachment metadata to rows collection (like manual tasks do).

        Args:
            db: Database session
            attachment_id: The ID of the attachment to add metadata for
            rows: The list of rows to add the attachment metadata to
        """
        attachment_record = (
            db.query(Attachment).filter(Attachment.id == attachment_id).first()
        )

        if attachment_record:
            try:
                size, url = attachment_record.retrieve_attachment()
                attachment_info = {
                    "file_name": attachment_record.file_name,
                    "download_url": str(url) if url else None,
                    "file_size": size,
                }
            except Exception as exc:
                logger.warning(
                    f"Could not retrieve attachment content for {attachment_record.file_name}: {exc}"
                )
                attachment_info = {
                    "file_name": attachment_record.file_name,
                    "download_url": None,
                    "file_size": None,
                }

            # Add attachment to the polling results
            attachments_item = None
            for item in rows:
                if isinstance(item, dict) and "retrieved_attachments" in item:
                    attachments_item = item
                    break

            if attachments_item is None:
                attachments_item = {"retrieved_attachments": []}
                rows.append(attachments_item)

            attachments_item["retrieved_attachments"].append(attachment_info)
