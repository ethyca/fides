"""
Service for attachment storage operations.

This service handles all storage-related operations for attachments,
keeping the Attachment model focused on data representation only.
"""

from typing import IO, Any, Optional, Tuple

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

    Provides methods for uploading, retrieving, and deleting
    attachments from storage backends (S3, GCS, local filesystem).

    Args:
        db: Database session for attachment operations. Optional for
            storage-only operations (upload, retrieve_url, retrieve_content,
            delete_from_storage).
    """

    def __init__(self, db: Optional[Session] = None):
        """Initialize the service with an optional database session."""
        self.db = db

    def _require_db(self) -> Session:
        """Get the db session, raising if not available."""
        if self.db is None:
            raise ValueError(
                "Database session required for this operation. "
                "Initialize AttachmentService with a db session."
            )
        return self.db

    def get_attachment(self, attachment_id: str) -> Optional[Attachment]:
        """Get an attachment by ID.

        Args:
            attachment_id: The ID of the attachment to retrieve.

        Returns:
            The Attachment if found, None otherwise.
        """
        db = self._require_db()
        return Attachment.get_by_key_or_id(db, data={"id": attachment_id})

    def _get_provider_and_bucket(self, attachment: Attachment) -> Tuple[Any, str]:
        """Get the storage provider and bucket for an attachment's config.

        Args:
            attachment: The attachment to get provider/bucket for.

        Returns:
            Tuple of (StorageProvider, bucket_name)
        """
        provider = StorageProviderFactory.create(attachment.config)
        bucket = StorageProviderFactory.get_bucket_from_config(attachment.config)
        return provider, bucket

    def upload(self, attachment: Attachment, file_data: IO[bytes]) -> None:
        """Upload attachment content to storage.

        Args:
            attachment: The attachment model with storage configuration.
            file_data: File-like object containing the data to upload.

        Raises:
            ValueError: If the file extension is invalid or not allowed.
        """
        provider, bucket = self._get_provider_and_bucket(attachment)

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
        # Get storage type value safely for logging
        storage_type = attachment.config.type
        storage_type_str = (
            storage_type.value if hasattr(storage_type, "value") else str(storage_type)
        )
        logger.info(
            "Uploaded {} to {} storage at {}/{} (size: {})",
            attachment.file_name,
            storage_type_str,
            bucket_name,
            attachment.id,
            result.file_size,
        )

    def retrieve_url(self, attachment: Attachment) -> Tuple[int, AnyHttpUrlString]:
        """Get presigned URL for attachment download.

        Args:
            attachment: The attachment to retrieve.

        Returns:
            Tuple of (file_size, presigned_url)
        """
        provider, bucket = self._get_provider_and_bucket(attachment)

        size = provider.get_file_size(bucket, attachment.file_key)
        url = provider.generate_presigned_url(
            bucket, attachment.file_key, MAX_TTL_SECONDS
        )

        return size, url

    def retrieve_content(self, attachment: Attachment) -> Tuple[int, IO[bytes]]:
        """Download attachment content.

        Args:
            attachment: The attachment to download.

        Returns:
            Tuple of (file_size, file_content)
        """
        provider, bucket = self._get_provider_and_bucket(attachment)

        size = provider.get_file_size(bucket, attachment.file_key)
        content = provider.download(bucket, attachment.file_key)

        return size, content

    def delete_from_storage(self, attachment: Attachment) -> None:
        """Delete attachment from storage.

        Args:
            attachment: The attachment to delete from storage.
        """
        provider, bucket = self._get_provider_and_bucket(attachment)

        # Use delete_prefix to delete the attachment folder (id/)
        prefix = f"{attachment.id}/"
        provider.delete_prefix(bucket, prefix)

    def create_and_upload(
        self,
        data: dict[str, Any],
        file_data: IO[bytes],
        references: Optional[list[dict[str, str]]] = None,
        check_name: bool = False,
    ) -> Attachment:
        """Create attachment record, upload file, and optionally create references.

        Creates a new attachment record in the database, uploads the file to
        storage, and creates any specified references. If upload fails, the
        database record is rolled back.

        Args:
            data: Attachment data dictionary with keys: file_name, user_id,
                attachment_type, storage_key.
            file_data: File-like object to upload.
            references: Optional list of reference dicts with keys:
                - reference_id: ID of the entity to reference
                - reference_type: Type from AttachmentReferenceType enum
            check_name: Whether to check for name conflicts.

        Returns:
            The created Attachment model.

        Raises:
            Exception: If upload fails (after rolling back DB record).
        """
        db = self._require_db()

        # Create the attachment record using Attachment.create
        attachment = Attachment.create(db=db, data=data, check_name=check_name)

        try:
            self.upload(attachment, file_data)

            # Create references if provided
            if references:
                for ref in references:
                    AttachmentReference.create(
                        db=db,
                        data={
                            "attachment_id": attachment.id,
                            "reference_id": ref["reference_id"],
                            "reference_type": ref["reference_type"],
                        },
                    )

            return attachment
        except Exception as e:
            logger.error("Failed to upload attachment: {}", e)
            # Delete the DB record since upload failed
            db.delete(attachment)
            db.flush()
            raise

    def delete(self, attachment: Attachment) -> None:
        """Delete attachment from DB and storage.

        Removes the attachment file from storage and deletes
        the database record along with all references.

        Args:
            attachment: The attachment to delete.
        """
        db = self._require_db()

        # Delete from storage first
        self.delete_from_storage(attachment)

        # Delete all references to the attachment
        for reference in attachment.references:
            db.delete(reference)

        # Delete the attachment record
        db.delete(attachment)
        db.commit()

    def delete_for_reference(
        self, reference_id: str, reference_type: AttachmentReferenceType
    ) -> None:
        """Delete all attachments for a given reference.

        Deletes all attachments associated with a given reference_id
        and reference_type, including their storage files and references.

        Args:
            reference_id: ID of the reference.
            reference_type: Type of the reference.

        Examples:
            Delete all attachments associated with a comment:
                attachment_service.delete_for_reference(
                    comment.id, AttachmentReferenceType.comment
                )

            Delete all attachments associated with a privacy request:
                attachment_service.delete_for_reference(
                    privacy_request.id, AttachmentReferenceType.privacy_request
                )
        """
        db = self._require_db()

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
            self.delete(attachment)
