from enum import Enum as EnumType
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser  # pylint: disable=unused-import


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

    user_id = Column(String, ForeignKey("fidesuser.id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String, nullable=False)
    attachment_type = Column(EnumColumn(AttachmentType), nullable=False)

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

    async def upload_attachment_to_s3(self, attachment: bytes) -> None:
        """Upload an attachment to S3 to the storage_url."""
        raise NotImplementedError("This method is not yet implemented")
        # AuditLog.create(
        #     db=db,
        #     data={
        #         "user_id": "system",
        #         "privacy_request_id": privacy_request.id,
        #         "action": AuditLogAction.attachment_uploaded,
        #         "message": "",
        #     },
        # )

    async def retrieve_attachment_from_s3(self) -> bytes:
        """Retrieve an attachment from S3."""
        raise NotImplementedError("This method is not yet implemented")
        # AuditLog.create(
        #     db=db,
        #     data={
        #         "user_id": "system",
        #         "privacy_request_id": privacy_request.id,
        #         "action": AuditLogAction.attachment_retrieved,
        #         "message": "",
        #     },
        # )

    async def delete_attachment_from_s3(self) -> None:
        """Delete an attachment from S3."""
        raise NotImplementedError("This method is not yet implemented")
        # AuditLog.create(
        #     db=db,
        #     data={
        #         "user_id": "system",
        #         "privacy_request_id": privacy_request.id,
        #         "action": AuditLogAction.attachment_deleted,
        #         "message": "",
        #     },
        # )

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
        # attachment_record.upload_attachment_to_s3(db, attachment)
        # log.info(f"Uploaded attachment {attachment_record.id} to S3")
        return super().create(db=db, data=data, check_name=check_name)

    def delete(self, db: Session) -> None:
        """Deletes an attachment record from the database and deletes the attachment from S3."""
        # attachment_record = cls.get(db, id)
        # attachment_record.delete_attachment_from_s3(db)
        # log.info(f"Deleted attachment {attachment_record.id} from S3")
        super().delete(db=db)
