"""
AttachmentService handles all attachment operations.
Complete abstraction for attachment lifecycle: create, persist, store, retrieve, delete.
"""

from io import BytesIO
from typing import IO, Any, Dict, Tuple

from fideslang.validation import AnyHttpUrlString
from loguru import logger as log
from sqlalchemy.orm import Session

from fides.api.models.attachment import Attachment, AttachmentReference
from fides.service.storage import StorageService

# 7 days in seconds - max allowed expiration time for presigned URLs
MAX_TTL_SECONDS = 604800


class AttachmentService:
    """
    Service for handling complete attachment lifecycle operations.

    Takes raw data, creates models, handles database persistence and storage operations.
    Provides a clean, high-level interface for attachment management.
    """

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        log.info("Initialized AttachmentService")

    def create_and_upload(
        self,
        *,
        attachment_data: Dict[str, Any],
        attachment_file: IO[bytes],
        references: list[dict[str, str]] = None,
    ):
        """
        Create attachment record, upload file to storage, and create entity references.

        Args:
            attachment_data: Raw attachment data (file_name, user_id, attachment_type, storage_key, etc.)
            attachment_file: File content to upload
            references: List of entity references [{"reference_id": "123", "reference_type": "privacy_request"}]

        Returns:
            Created Attachment instance

        Raises:
            Exception: If creation or upload fails
        """

        # Create attachment record in database
        attachment = Attachment.create(db=self.db, data=attachment_data)

        try:
            # Upload file to storage
            self._upload_to_storage(attachment, attachment_file)

            # Create entity references if provided
            if references:
                self._create_references(attachment.id, references)

            log.info(f"Successfully created and uploaded attachment {attachment.id}")
            return attachment
        except Exception as e:
            # If upload fails, clean up the database record
            log.error(
                f"Upload failed for attachment {attachment.id}, cleaning up DB record: {e}"
            )
            attachment.delete_from_db_only(self.db)
            raise e

    def get_by_id(self, attachment_id: str):
        """Get attachment by ID."""

        attachment = Attachment.get_by_key_or_id(self.db, data={"id": attachment_id})
        if not attachment:
            raise ValueError(f"Attachment not found: {attachment_id}")
        return attachment

    def get_download_info(self, attachment) -> Tuple[int, AnyHttpUrlString]:
        """Get attachment size and download URL."""
        try:
            storage_service = StorageService.from_config(attachment.config)

            # Get file metadata
            response = storage_service.retrieve_file(
                attachment.file_key, get_content=False
            )
            if not response.success:
                if "File not found" in response.error_message:
                    raise FileNotFoundError(f"Attachment file not found: {attachment.file_key}")
                else:
                    raise Exception(f"Failed to get metadata: {response.error_message}")

            # Generate presigned URL
            presigned_url = storage_service.generate_presigned_url(
                attachment.file_key, ttl_seconds=MAX_TTL_SECONDS
            )

            file_size = response.file_size or 0
            log.info(
                f"Retrieved download info for {attachment.id} (size: {file_size} bytes)"
            )

            return file_size, presigned_url

        except Exception as e:
            log.error(f"Failed to get download info for {attachment.id}: {e}")
            raise

    def get_content(self, attachment) -> Tuple[int, BytesIO]:
        """Get attachment content for processing."""
        try:
            storage_service = StorageService.from_config(attachment.config)

            # Use streaming download for memory efficiency
            with storage_service.stream_download(attachment.file_key) as content_stream:
                content = BytesIO(content_stream.read())
                content.seek(0)  # Reset pointer

            file_size = len(content.getvalue())
            log.info(f"Retrieved content for {attachment.id} (size: {file_size} bytes)")

            return file_size, content

        except Exception as e:
            log.error(f"Failed to get content for {attachment.id}: {e}")
            # Check if this is an S3 error wrapped by smart_open and re-raise the original error
            if hasattr(e, 'backend_error'):
                raise e.backend_error
            raise

    def delete_completely(self, attachment) -> None:
        """Delete attachment from both storage and database."""
        # Delete from storage first (logs warnings if fails, doesn't raise)
        self._delete_from_storage(attachment)

        # Always delete from database regardless of storage outcome
        attachment.delete_from_db_only(self.db)
        log.info(f"Completely deleted attachment {attachment.id}")

    def _upload_to_storage(self, attachment, attachment_file: IO[bytes]) -> None:
        """Upload an attachment file to storage."""
        try:
            # Validate attachment_file parameter
            if attachment_file is None:
                # Import here to avoid circular imports
                from botocore.exceptions import ClientError
                raise ClientError(
                    error_response={
                        'Error': {
                            'Code': 'InvalidParameterValue',
                            'Message': "Failed to upload attachment: The 'document' parameter must be a file-like object"
                        }
                    },
                    operation_name='UploadAttachment'
                )

            storage_service = StorageService.from_config(attachment.config)

            # Reset file pointer to beginning
            try:
                attachment_file.seek(0)
            except Exception as e:
                raise ValueError(f"Failed to reset file pointer: {e}")

            # Store file
            response = storage_service.store_file(
                file_content=attachment_file,
                file_key=attachment.file_key,
                content_type=attachment.content_type,
                metadata={
                    "attachment_id": attachment.id,
                    "file_name": attachment.file_name,
                    "attachment_type": attachment.attachment_type.value,
                    "user_id": attachment.user_id,
                    "created_by": "AttachmentService",
                },
            )

            if not response.success:
                raise Exception(f"Storage upload failed: {response.error_message}")

            log.info(
                f"Uploaded attachment {attachment.id}/{attachment.file_name} to storage"
            )

        except Exception as e:
            log.error(
                f"Storage upload failed for {attachment.id}/{attachment.file_name}: {e}"
            )
            raise

    def _delete_from_storage(self, attachment) -> None:
        """Delete an attachment file from storage."""
        try:
            storage_service = StorageService.from_config(attachment.config)
            response = storage_service.delete_file(attachment.file_key)

            if not response.success:
                log.warning(
                    f"Storage deletion failed for {attachment.id}: {response.error_message}"
                )
                # Don't raise - we still want DB deletion to proceed
            else:
                log.info(
                    f"Deleted attachment {attachment.id}/{attachment.file_name} from storage"
                )

        except Exception as e:
            log.error(
                f"Storage deletion error for {attachment.id}/{attachment.file_name}: {e}"
            )
            # Don't raise - we still want DB deletion to proceed

    def add_references(self, attachment, references: list[dict[str, str]]) -> None:
        """Add references to associate attachment with different entities."""
        self._create_references(attachment.id, references)

    def get_attachments_for_entity(self, entity_id: str, reference_type: str) -> list:
        """Get all attachments associated with a specific entity."""

        attachment_refs = (
            self.db.query(AttachmentReference)
            .filter(
                AttachmentReference.reference_id == entity_id,
                AttachmentReference.reference_type == reference_type,
            )
            .all()
        )

        return [ref.attachment for ref in attachment_refs if ref.attachment]

    def _create_references(
        self, attachment_id: str, references: list[dict[str, str]]
    ) -> None:
        """Create attachment references to associate with different entities."""

        for ref in references:
            reference_data = {
                "attachment_id": attachment_id,
                "reference_id": ref["reference_id"],
                "reference_type": ref["reference_type"],
            }
            AttachmentReference.create(db=self.db, data=reference_data)
            log.info(
                f"Created reference: attachment {attachment_id} -> {ref['reference_type']} {ref['reference_id']}"
            )

    def delete_attachments_for_entity(self, entity_id: str, reference_type) -> None:
        """
        Delete all attachments associated with a specific entity.

        This method handles both storage cleanup and database cleanup for all attachments
        associated with an entity (privacy request, comment, manual task submission, etc.).

        Args:
            entity_id: The ID of the entity whose attachments should be deleted
            reference_type: The type of reference (AttachmentReferenceType enum value)
        """

        # Find all attachment references for this entity
        attachment_refs = (
            self.db.query(AttachmentReference)
            .filter(
                AttachmentReference.reference_id == entity_id,
                AttachmentReference.reference_type == reference_type,
            )
            .all()
        )

        deleted_count = 0
        for attachment_ref in attachment_refs:
            if attachment_ref.attachment:
                try:
                    # Delete attachment completely (storage + database)
                    self.delete_completely(attachment_ref.attachment)
                    deleted_count += 1
                except Exception as e:
                    log.error(
                        f"Failed to delete attachment {attachment_ref.attachment.id} "
                        f"for entity {entity_id}: {e}"
                    )
                    # Continue with other attachments even if one fails

        log.info(
            f"Deleted {deleted_count} attachments for entity {entity_id} "
            f"(reference_type: {reference_type})"
        )

    @staticmethod
    def delete_attachments_for_reference_and_type(
        db: Session, reference_id: str, reference_type
    ) -> None:
        """
        Static method for backward compatibility.

        Deletes all attachment records and their associated files from storage
        for the given reference_id and reference_type.

        Args:
            db: Database session
            reference_id: The ID of the entity whose attachments should be deleted
            reference_type: The type of reference (AttachmentReferenceType)
        """
        attachment_service = AttachmentService(db)
        attachment_service.delete_attachments_for_entity(reference_id, reference_type)
