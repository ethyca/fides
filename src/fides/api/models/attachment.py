import os
from enum import Enum as EnumType
from functools import wraps
from typing import Any, Callable, Optional

from boto3 import Session as S3Session
from fideslang.validation import AnyHttpUrlString
from loguru import logger as log
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser  # pylint: disable=unused-import
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from fides.api.tasks.storage import (
    LOCAL_FIDES_UPLOAD_DIRECTORY,
    create_presigned_url_for_s3,
)
from fides.api.util.aws_util import get_aws_session


def with_config(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(
        self: "Attachment", db: Session, *args: Any, **kwargs: Any
    ) -> Optional[StorageConfig]:
        config = self.config(db)
        if config is None:
            self.config_error_handler()
            return None
        return method(self, db, config, *args, **kwargs)

    return wrapper  # type: ignore


def get_s3_client(config: StorageConfig) -> S3Session:
    """Returns an AWS S3 client based on a StorageConfig"""
    session = get_aws_session(
        auth_method=config.details[StorageDetails.AUTH_METHOD.value],
        storage_secrets=config.secrets,
    )
    return session.client("s3")


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
    storage_key = Column(String, nullable=False)

    user = relationship(
        "FidesUser",
        backref="attachments",
        lazy="selectin",
        uselist=False,
    )

    references = relationship(
        "AttachmentReference",
        back_populates="attachment",
        cascade="all, delete",
        uselist=True,
    )

    def config(self, db: Session) -> Optional[StorageConfig]:
        """Returns the storage config for the attachment."""
        return StorageConfig.get_by(db=db, field="key", value=self.storage_key)

    def config_error_handler(self) -> None:
        log.error(f"Storage config not found for key: {self.storage_key}")
        raise ValueError(f"Storage config not found for key: {self.storage_key}")

    @with_config
    def upload(self, db: Session, config: Any, attachment: bytes) -> None:
        """Uploads an attachment to S3 or local storage."""
        if config.type == StorageType.s3:
            bucket_name = f"{config.details[StorageDetails.BUCKET.value]}"
            s3_client = get_s3_client(config)
            s3_client.put_object(Bucket=bucket_name, Key=self.id, Body=attachment)
            log.info(f"Uploaded {self.file_name} to S3 bucket {bucket_name}/{self.id}")
            return

        if config.type == StorageType.local:
            if not os.path.exists(LOCAL_FIDES_UPLOAD_DIRECTORY):
                os.makedirs(LOCAL_FIDES_UPLOAD_DIRECTORY)

            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
            with open(filename, "wb") as file:
                file.write(attachment)
            return

        raise ValueError(f"Unsupported storage type: {config.type}")

    @with_config
    def download_attachment_from_s3(
        self, db: Session, config: Any
    ) -> Optional[AnyHttpUrlString]:
        """Returns the presigned URL for an attachment in S3."""
        if config.type != StorageType.s3:
            raise ValueError(f"Unsupported storage: {config.type}")

        bucket_name = f"{config.details[StorageDetails.BUCKET.value]}"
        s3_client = get_s3_client(config)
        return create_presigned_url_for_s3(s3_client, bucket_name, self.id)

    @with_config
    def retrieve_attachment(self, db: Session, config: Any) -> Optional[bytes]:
        """Returns the attachment from S3 in bytes form."""
        if config.type == StorageType.s3:
            bucket_name = f"{config.details[StorageDetails.BUCKET.value]}"
            s3_client = get_s3_client(config)
            response = s3_client.get_object(Bucket=bucket_name, Key=self.id)
            return response["Body"].read()

        if config.type == StorageType.local:
            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
            with open(filename, "rb") as file:
                return file.read()

        raise ValueError(f"Unsupported storage type: {config.type}")

    def delete_attachment_from_storage(self, db: Session, config: Any) -> None:
        """Deletes an attachment from S3 or local storage."""
        if config.type == StorageType.s3:
            bucket_name = f"{config.details[StorageDetails.BUCKET.value]}"
            s3_client = get_s3_client(config)
            s3_client.delete_object(Bucket=bucket_name, Key=self.id)
            log.info(f"Deleted {self.file_name} from S3 bucket {bucket_name}/{self.id}")
            return

        if config.type == StorageType.local:
            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
            os.remove(filename)
            return

        raise ValueError(f"Unsupported storage type: {config.type}")

    @classmethod
    def create_and_upload(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        attachment_file: bytes,
        check_name: bool = False,
    ) -> "Attachment":
        """Creates a new attachment record in the database and uploads the attachment to S3."""
        if attachment_file is None:
            raise ValueError("Attachment is required")
        attachment_model = super().create(db=db, data=data, check_name=check_name)

        try:
            attachment_model.upload(db, attachment_file)
        except Exception as e:
            log.error(f"Failed to upload attachment: {e}")
            db.rollback()
            raise e
        return attachment_model

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

    @with_config
    def delete(self, db: Session, config: Any) -> None:
        """Deletes an attachment record from the database and deletes the attachment from S3."""
        self.delete_attachment_from_storage(db, config)
        super().delete(db=db)
