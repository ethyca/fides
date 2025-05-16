import os
from enum import Enum as EnumType
from typing import IO, TYPE_CHECKING, Any, Tuple

from fideslang.validation import AnyHttpUrlString
from loguru import logger as log
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint, orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.service.storage.s3 import (
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
)
from fides.api.service.storage.util import get_local_filename

if TYPE_CHECKING:
    from fides.api.models.comment import Comment
    from fides.api.models.fides_user import FidesUser
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.models.storage import StorageConfig


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


class AttachmentReference(Base):
    """
    Stores information about an Attachment and any other element which may reference that attachment.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "attachment_reference"

    attachment_id = Column(
        String, ForeignKey("attachment.id", ondelete="CASCADE"), nullable=False
    )
    reference_id = Column(String, nullable=False)
    reference_type = Column(EnumColumn(AttachmentReferenceType), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "attachment_id", "reference_id", name="_attachment_reference_uc"
        ),
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

    def upload(self, attachment: IO[bytes]) -> None:
        """Uploads an attachment to S3 or local storage."""
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            generic_upload_to_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=f"{self.id}/{self.file_name}",
                document=attachment,
                auth_method=auth_method,
            )
            log.info(f"Uploaded {self.file_name} to S3 bucket {bucket_name}/{self.id}")
            return

        if self.config.type == StorageType.local:
            filename = get_local_filename(f"{self.id}/{self.file_name}")

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
        Retrieves a the size of the attachment and the presigned URL to retrieve it.
        - For s3:
          - the size is retrieved from the s3 object metadata
          - the presigned URL is retrieved from the s3 client
        - For local:
          - the size is retrieved from the file size
          - the URL is the local file path
        """
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            size, url = generic_retrieve_from_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=f"{self.id}/{self.file_name}",
                auth_method=auth_method,
            )
            return size, url

        if self.config.type == StorageType.local:
            filename = get_local_filename(f"{self.id}/{self.file_name}")
            with open(filename, "rb") as file:
                size = len(file.read())
                return size, filename

        raise ValueError(f"Unsupported storage type: {self.config.type}")

    def delete_attachment_from_storage(self) -> None:
        """Deletes an attachment from S3 or local storage."""
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            generic_delete_from_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=f"{self.id}/{self.file_name}",
                auth_method=auth_method,
            )
            return

        if self.config.type == StorageType.local:
            filename = get_local_filename(f"{self.id}/{self.file_name}")
            os.remove(filename)
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
