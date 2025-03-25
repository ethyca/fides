import os
from enum import Enum as EnumType
from typing import IO, Any, Optional

from loguru import logger as log
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser  # pylint: disable=unused-import
from fides.api.models.storage import StorageConfig  # pylint: disable=unused-import
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.service.storage.s3 import (
    generic_delete_from_s3,
    generic_retrieve_from_s3,
    generic_upload_to_s3,
)
from fides.api.service.storage.util import (
    LOCAL_FIDES_UPLOAD_DIRECTORY,
    get_local_filename,
)


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

    manual_step = "manual_step"
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

    attachment_id = Column(String, ForeignKey("attachment.id"), nullable=False)
    reference_id = Column(String, nullable=False)
    reference_type = Column(EnumColumn(AttachmentReferenceType), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "attachment_id", "reference_id", name="_attachment_reference_uc"
        ),
    )

    attachment = relationship(
        "Attachment",
        back_populates="references",
        uselist=False,
    )

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
        cascade="all, delete",
        uselist=True,
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
                file_key=self.id,
                document=attachment,
                auth_method=auth_method,
            )
            log.info(f"Uploaded {self.file_name} to S3 bucket {bucket_name}/{self.id}")
            return

        if self.config.type == StorageType.local:
            filename = get_local_filename(self.id)
            with open(filename, "wb") as file:
                file.write(attachment.read())
            return

        raise ValueError(f"Unsupported storage type: {self.config.type}")

    def retrieve_attachment(self) -> Optional[bytes]:
        """Returns the attachment from S3 in bytes form."""
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            return generic_retrieve_from_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=self.id,
                auth_method=auth_method,
            )

        if self.config.type == StorageType.local:
            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
            with open(filename, "rb") as file:
                return file.read(), filename

        raise ValueError(f"Unsupported storage type: {self.config.type}")

    def delete_attachment_from_storage(self) -> None:
        """Deletes an attachment from S3 or local storage."""
        if self.config.type == StorageType.s3:
            bucket_name = f"{self.config.details[StorageDetails.BUCKET.value]}"
            auth_method = self.config.details[StorageDetails.AUTH_METHOD.value]
            generic_delete_from_s3(
                storage_secrets=self.config.secrets,
                bucket_name=bucket_name,
                file_key=self.id,
                auth_method=auth_method,
            )
            return

        if self.config.type == StorageType.local:
            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
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
        """Creates a new attachment record in the database and uploads the attachment to S3."""
        if attachment_file is None:
            raise ValueError("Attachment is required")
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
        super().delete(db=db)
