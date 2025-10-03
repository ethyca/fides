import os
from enum import Enum as EnumType
from io import BytesIO
from typing import IO, TYPE_CHECKING, Any, Tuple

from fideslang.validation import AnyHttpUrlString
from loguru import logger as log
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func, orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.s3 import (
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
)
from fides.api.service.storage.util import AllowedFileType, get_local_filename

if TYPE_CHECKING:
    from fides.api.models.comment import Comment
    from fides.api.models.fides_user import FidesUser
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.models.storage import StorageConfig


# This is 7 days in seconds and is currently the max allowed
# configurable expiration time for presigned URLs for both s3 and gcs.
MAX_TTL_SECONDS = 604800


class AttachmentType(str, EnumType):
    """
    Enum for attachment types. Indicates attachment usage.
    """

    internal_use_only = "internal_use_only"
    include_with_access_package = "include_with_access_package"


class AttachmentReferenceType(str, EnumType):
    """
    Enum for attachment reference types. Indicates where attachment is referenced.
    """

    access_manual_webhook = "access_manual_webhook"
    erasure_manual_webhook = "erasure_manual_webhook"
    privacy_request = "privacy_request"
    comment = "comment"
    manual_task_submission = "manual_task_submission"
    request_task = "request_task"


class AttachmentReference(Base):
    """
    Stores information about an Attachment and any other element which may reference that attachment.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "attachment_reference"

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    attachment_id = Column(
        String,
        ForeignKey("attachment.id", name="attachment_reference_attachment_id_fkey"),
        nullable=False,
    )
    reference_id = Column(String, nullable=False)
    reference_type = Column(EnumColumn(AttachmentReferenceType), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "attachment_id", "reference_id", name="_attachment_reference_uc"
        ),
        Index("ix_attachment_reference_reference_id", "reference_id"),
        Index("ix_attachment_reference_reference_type", "reference_type"),
    )

    # Relationships
    attachment = relationship("Attachment", back_populates="references")

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = False
    ) -> "AttachmentReference":
        """Creates a new attachment reference record in the database."""
        return super().create(db=db, data=data, check_name=check_name)


class Attachment(Base):
    """
    Stores information about an Attachment.
    """

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_id = Column(
        String, ForeignKey("fidesuser.id", ondelete="SET NULL"), nullable=True
    )
    file_name = Column(String, nullable=False)
    attachment_type = Column(EnumColumn(AttachmentType), nullable=False)
    storage_key = Column(
        String, ForeignKey("storageconfig.key", ondelete="CASCADE"), nullable=False
    )

    user = relationship(
        "FidesUser",
        lazy="selectin",
        uselist=False,
    )

    references = relationship(
        "AttachmentReference",
        back_populates="attachment",
        cascade="all, delete-orphan",
        uselist=True,
        foreign_keys=[AttachmentReference.attachment_id],
        primaryjoin=lambda: Attachment.id
        == orm.foreign(AttachmentReference.attachment_id),
    )

    config = relationship(
        "StorageConfig",
        lazy="selectin",
        uselist=False,
    )

    @property
    def content_type(self) -> str:
        """Returns the content type of the attachment."""
        return AllowedFileType[self.file_name.split(".")[-1]].value

    @property
    def file_key(self) -> str:
        """Returns the file key of the attachment."""
        return f"{self.id}/{self.file_name}"

    def upload(self, attachment: IO[bytes]) -> None:
        """Uploads an attachment to S3, GCS, or local storage."""
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            generic_upload_to_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=self.file_key,
                document=attachment,
                auth_method=auth_method,
            )
            log.info(f"Uploaded {self.file_name} to S3 bucket {bucket_name}/{self.id}")
            return

        if self.config.type == StorageType.gcs:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            storage_client = get_gcs_client(auth_method, self.config.secrets)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(self.file_key)

            # Reset the file pointer to the beginning
            try:
                attachment.seek(0)
            except Exception as e:
                raise ValueError(f"Failed to reset file pointer for attachment: {e}")

            blob.upload_from_file(attachment)
            log.info(f"Uploaded {self.file_name} to GCS bucket {bucket_name}/{self.id}")
            return

        if self.config.type == StorageType.local:
            filename = get_local_filename(self.file_key)

            # Validate that attachment is a file-like object
            if not hasattr(attachment, "read"):
                raise TypeError(f"Expected a file-like object, got {type(attachment)}")

            # Reset the file pointer to the beginning
            try:
                attachment.seek(0)
            except Exception as e:
                raise ValueError(f"Failed to reset file pointer for attachment: {e}")

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Write the file in chunks to avoid loading the entire content into memory
            with open(filename, "wb") as file:
                for chunk in iter(
                    lambda: attachment.read(1024 * 1024), b""
                ):  # 1 MB chunks
                    if not isinstance(chunk, bytes):
                        raise TypeError(f"Expected bytes, got {type(chunk)}")
                    file.write(chunk)

            log.info(f"Uploaded {self.file_name} to local storage at {filename}")
            return

        raise ValueError(f"Unsupported storage type: {self.config.type}")

    def retrieve_attachment(
        self,
    ) -> Tuple[int, AnyHttpUrlString]:
        """
        Retrieves the size of the attachment and a presigned/signed URL.
        - For s3:
          - the size is retrieved from the s3 object metadata
          - returns presigned URL
        - For gcs:
          - the size is retrieved from the blob metadata
          - returns signed URL
        - For local:
          - the size is retrieved from the file size
          - returns the local file path
        """
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            size, url = generic_retrieve_from_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=self.file_key,
                auth_method=auth_method,
                get_content=False,
                ttl_seconds=MAX_TTL_SECONDS,
            )
            return size, url

        if self.config.type == StorageType.gcs:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            storage_client = get_gcs_client(auth_method, self.config.secrets)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(self.file_key)

            # Ensure we have the blob metadata
            blob.reload()
            # Expiration is set to 7 days
            url = blob.generate_signed_url(
                version="v4",
                expiration=MAX_TTL_SECONDS,
                method="GET",
            )
            return blob.size, url

        if self.config.type == StorageType.local:
            filename = get_local_filename(self.file_key)
            size = os.path.getsize(filename)
            return size, filename

        raise ValueError(f"Unsupported storage type: {self.config.type}")

    def retrieve_attachment_content(
        self,
    ) -> Tuple[int, IO[bytes]]:
        """
        Retrieves the size of the attachment and its actual content.
        - For s3:
          - the size is retrieved from the s3 object metadata
          - returns the actual content
        - For gcs:
          - the size is retrieved from the blob metadata
          - returns the actual content
        - For local:
          - the size is retrieved from the file size
          - returns the actual content
        """
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            size, fileobj = generic_retrieve_from_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=self.file_key,
                auth_method=auth_method,
                get_content=True,
            )
            return size, fileobj

        if self.config.type == StorageType.gcs:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            storage_client = get_gcs_client(auth_method, self.config.secrets)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(self.file_key)

            fileobj = BytesIO()
            blob.download_to_file(fileobj)
            fileobj.seek(0)  # Reset pointer to beginning after download
            return blob.size, fileobj

        if self.config.type == StorageType.local:
            filename = get_local_filename(self.file_key)
            size = os.path.getsize(filename)
            with open(filename, "rb") as fileobj:
                content = BytesIO(fileobj.read())
                content.seek(0)  # Reset pointer to beginning
                return size, content

        raise ValueError(f"Unsupported storage type: {self.config.type}")

    def delete_attachment_from_storage(self) -> None:
        """Deletes an attachment from S3, GCS, or local storage."""
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            generic_delete_from_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=self.file_key,
                auth_method=auth_method,
            )
            return

        if self.config.type == StorageType.gcs:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            storage_client = get_gcs_client(auth_method, self.config.secrets)
            bucket = storage_client.bucket(bucket_name)

            # List and delete all blobs in the folder
            prefix = f"{self.id}/"
            blobs = bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                blob.delete()
            return

        if self.config.type == StorageType.local:
            folder_path = os.path.dirname(get_local_filename(self.file_key))
            if os.path.exists(folder_path):
                import shutil

                shutil.rmtree(folder_path)
            return

        raise ValueError(f"Unsupported storage type: {self.config.type}")

    @classmethod
    def create_and_upload(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        attachment_file: IO[bytes],
        check_name: bool = False,
    ) -> "Attachment":
        """Creates a new attachment record in the database and uploads the attachment via the upload method."""
        attachment_model = super().create(db=db, data=data, check_name=check_name)

        try:
            attachment_model.upload(attachment_file)
            return attachment_model
        except Exception as e:
            log.error(f"Failed to upload attachment: {e}")
            attachment_model.delete(db)
            raise e

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "Attachment":
        """Raises Error, provides information for user to create with upload instead."""
        raise NotImplementedError("Please use create_and_upload method for Attachment")

    def delete(self, db: Session) -> None:
        """Deletes an attachment record from the database and deletes the attachment from S3."""
        self.delete_attachment_from_storage()

        # Delete all references to the attachment
        for reference in self.references:
            reference.delete(db)
        super().delete(db=db)

    @staticmethod
    def delete_attachments_for_reference_and_type(
        db: Session, reference_id: str, reference_type: AttachmentReferenceType
    ) -> None:
        """
        Deletes attachments associated with a given reference_id and reference_type.
        Deletes all references to the attachments.

        Args:
            db: Database session
            reference_id: ID of the reference
            reference_type: Type of the reference

        Examples:

        - Delete all attachments associated with a comment.
           ``Attachment.delete_attachments_for_reference_and_type(
               db, comment.id, AttachmentReferenceType.comment
           )``
        - Delete all attachments associated with a privacy request.
           ``Attachment.delete_attachments_for_reference_and_type(
               db, privacy_request.id, AttachmentReferenceType.privacy_request
            )``
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
            attachment.delete(db)
