import os
from enum import Enum as EnumType
from typing import Any, Optional

from fideslang.validation import FidesKey
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser  # pylint: disable=unused-import
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.fides_user import FidesUser
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import AWSAuthMethod, StorageDetails, StorageSecrets, StorageType
from fides.api.tasks.storage import create_presigned_url_for_s3, LOCAL_FIDES_UPLOAD_DIRECTORY
from fides.api.util.aws_util import get_aws_session
from loguru import logger as log


def get_s3_client(config):
    session = get_aws_session(
        auth_method=config.auth_method.value,
        storage_secrets=config.secrets
    )
    bucket_name = f"{config.details[StorageDetails.BUCKET.value]}"
    return bucket_name, session.client("s3")


def get_storage_config(db, storage_key) -> str:
        return StorageConfig.get_by(db=db, field="key", value=storage_key)


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

    def upload(self, db: Session, attachment: bytes, storage_key) -> None:
        """Uploads an attachment to S3 or local storage."""
        config = get_storage_config(db, storage_key)

        if config.type.value == StorageType.s3.value:
            bucket_name, s3_client = get_s3_client(config)
            s3_client.put_object(Bucket=bucket_name, Key=self.id, Body=attachment)
            log.info(f"Uploaded {self.file_name} to S3 bucket {bucket_name}/{self.id}")
        elif config.type.value == StorageType.local.value:
            if not os.path.exists(LOCAL_FIDES_UPLOAD_DIRECTORY):
                os.makedirs(LOCAL_FIDES_UPLOAD_DIRECTORY)

            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
            with open(filename, "wb") as file:
                file.write(attachment)
        else:
            raise ValueError(f"Unsupported storage type: {config.type}")

    def download_attachment_from_s3(self, db, storage_key) -> str:
        """Returns the presigned URL for an attachment in S3."""
        config = get_storage_config(db, storage_key)
        if config.type.value != StorageType.s3.value:
            raise ValueError(f"Unsupported storage: {config.type}")

        bucket_name, s3_client = get_s3_client(config)
        return create_presigned_url_for_s3(s3_client, bucket_name, self.id)

    def retrieve_attachment(self, db: Session, storage_key: str) -> bytes:
        """Returns the attachment from S3 in bytes form."""
        config = get_storage_config(db, storage_key)

        if config.type.value == StorageType.s3.value:
            bucket_name, s3_client = get_s3_client(config)
            response = s3_client.get_object(Bucket=bucket_name, Key=self.id)
            return response["Body"].read()
        elif config.type.value == StorageType.local.value:
            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
            with open(filename, "rb") as file:
                return file.read()
        else:
            raise ValueError(f"Unsupported storage type: {config.type}")

    def delete_attachment_from_storage(self, db: Session, storage_key: str) -> None:
        """Deletes an attachment from S3 or local storage."""
        config = get_storage_config(db, storage_key)

        if config.type.value == StorageType.s3.value:
            bucket_name, s3_client = get_s3_client(config)
            s3_client.delete_object(Bucket=bucket_name, Key=self.id)
            log.info(f"Deleted {self.file_name} from S3 bucket {bucket_name}/{self.id}")
        elif config.type.value == StorageType.local.value:
            filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{self.id}"
            os.remove(filename)
        else:
            raise ValueError(f"Unsupported storage type: {config.type}")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
        attachment: Optional[
            bytes
        ] = None,  # This will not be optional once the upload method is implemented.
    ) -> "Attachment":
        """Creates a new attachment record in the database and uploads the attachment to S3."""
        attachment_model = super().create(db=db, data=data, check_name=check_name)
        if attachment is not None:
            attachment_model.upload(db, attachment, storage_key)
        return attachment_model

    def delete(self, db: Session, storage_key) -> None:
        """Deletes an attachment record from the database and deletes the attachment from S3."""
        self.delete_attachment_from_storage(db, storage_key)
        super().delete(db=db)
