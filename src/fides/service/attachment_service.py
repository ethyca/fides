"""
Service for attachment storage operations.

This service handles all storage-related operations for attachments,
keeping the Attachment model focused on data representation only.
"""

from typing import IO, Any, Tuple

from fideslang.validation import AnyHttpUrlString
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
)
from fides.api.schemas.storage.storage import StorageDetails
from fides.api.service.storage.providers import StorageProviderFactory

# This is 7 days in seconds and is currently the max allowed
# configurable expiration time for presigned URLs for both s3 and gcs.
MAX_TTL_SECONDS = 604800


class AttachmentService:
    """Service for attachment storage operations.

    Provides static methods for uploading, retrieving, and deleting
    attachments from storage backends (S3, GCS, local filesystem).
    """

    @staticmethod
    def _get_provider_and_bucket(attachment: Attachment) -> Tuple[Any, str]:
        """Get the storage provider and bucket for an attachment's config.

        Args:
            attachment: The attachment to get provider/bucket for.

        Returns:
            Tuple of (StorageProvider, bucket_name)
        """
        provider = StorageProviderFactory.create(attachment.config)
        bucket = StorageProviderFactory.get_bucket_from_config(attachment.config)
        return provider, bucket

    @staticmethod
    def upload(attachment: Attachment, file_data: IO[bytes]) -> None:
        """Upload attachment content to storage.

        Args:
            attachment: The attachment model with storage configuration.
            file_data: File-like object containing the data to upload.

        Raises:
            ValueError: If the file extension is invalid or not allowed.
        """
        provider, bucket = AttachmentService._get_provider_and_bucket(attachment)

        # Validate content type (catches invalid file extensions)
        try:
            content_type = attachment.content_type
        except KeyError as e:
            raise ValueError(
                f"Invalid or unallowed file extension: {attachment.file_name}"
            ) from e

        result = provider.upload(
            bucket=bucket,
            key=attachment.file_key,
            data=file_data,
            content_type=content_type,
        )

        bucket_name = attachment.config.details.get(
            StorageDetails.BUCKET.value, "local"
        )
        logger.info(
            "Uploaded {} to {} storage at {}/{} (size: {})",
            attachment.file_name,
            attachment.config.type.value,
            bucket_name,
            attachment.id,
            result.file_size,
        )

    @staticmethod
    def retrieve_url(attachment: Attachment) -> Tuple[int, AnyHttpUrlString]:
        """Get presigned URL for attachment download.

        Args:
            attachment: The attachment to retrieve.

        Returns:
            Tuple of (file_size, presigned_url)
        """
        provider, bucket = AttachmentService._get_provider_and_bucket(attachment)

        size = provider.get_file_size(bucket, attachment.file_key)
        url = provider.generate_presigned_url(
            bucket, attachment.file_key, MAX_TTL_SECONDS
        )

        return size, url

    @staticmethod
    def retrieve_content(attachment: Attachment) -> Tuple[int, IO[bytes]]:
        """Download attachment content.

        Args:
            attachment: The attachment to download.

        Returns:
            Tuple of (file_size, file_content)
        """
        provider, bucket = AttachmentService._get_provider_and_bucket(attachment)

        size = provider.get_file_size(bucket, attachment.file_key)
        content = provider.download(bucket, attachment.file_key)

        return size, content

    @staticmethod
    def delete_from_storage(attachment: Attachment) -> None:
        """Delete attachment from storage.

        Args:
            attachment: The attachment to delete from storage.
        """
        provider, bucket = AttachmentService._get_provider_and_bucket(attachment)

        # Use delete_prefix to delete the attachment folder (id/)
        prefix = f"{attachment.id}/"
        provider.delete_prefix(bucket, prefix)

    @staticmethod
    def create_and_upload(
        db: Session,
        data: dict[str, Any],
        file_data: IO[bytes],
        check_name: bool = False,
    ) -> Attachment:
        """Create attachment record and upload file.

        Creates a new attachment record in the database and uploads
        the file to storage. If upload fails, the database record
        is rolled back.

        Args:
            db: Database session.
            data: Attachment data dictionary.
            file_data: File-like object to upload.
            check_name: Whether to check for name conflicts.

        Returns:
            The created Attachment model.

        Raises:
            Exception: If upload fails (after rolling back DB record).
        """
        # Import here to avoid circular imports - Base.create is used
        from fides.api.db.base_class import Base

        # Create the attachment record using Base.create directly
        attachment = Base.create.__func__(
            Attachment, db=db, data=data, check_name=check_name
        )

        try:
            AttachmentService.upload(attachment, file_data)
            return attachment
        except Exception as e:
            logger.error("Failed to upload attachment: {}", e)
            # Delete the DB record since upload failed
            db.delete(attachment)
            db.flush()
            raise

    @staticmethod
    def delete(db: Session, attachment: Attachment) -> None:
        """Delete attachment from DB and storage.

        Removes the attachment file from storage and deletes
        the database record along with all references.

        Args:
            db: Database session.
            attachment: The attachment to delete.
        """
        # Delete from storage first
        AttachmentService.delete_from_storage(attachment)

        # Delete all references to the attachment
        for reference in attachment.references:
            db.delete(reference)

        # Delete the attachment record
        db.delete(attachment)
        db.flush()

    @staticmethod
    def delete_for_reference(
        db: Session, reference_id: str, reference_type: AttachmentReferenceType
    ) -> None:
        """Delete all attachments for a given reference.

        Deletes all attachments associated with a given reference_id
        and reference_type, including their storage files and references.

        Args:
            db: Database session.
            reference_id: ID of the reference.
            reference_type: Type of the reference.

        Examples:
            Delete all attachments associated with a comment:
                AttachmentService.delete_for_reference(
                    db, comment.id, AttachmentReferenceType.comment
                )

            Delete all attachments associated with a privacy request:
                AttachmentService.delete_for_reference(
                    db, privacy_request.id, AttachmentReferenceType.privacy_request
                )
        """
        # Query attachments explicitly to avoid lazy loading
        attachments = (
            db.query(Attachment)
            .join(AttachmentReference)
            .filter(
                AttachmentReference.reference_id == reference_id,
                AttachmentReference.reference_type == reference_type,
            )
            .all()
        )

        for attachment in attachments:
            AttachmentService.delete(db, attachment)
