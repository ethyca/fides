from enum import Enum as EnumType
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    orm,
)
from sqlalchemy import Enum as EnumColumn
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.service.storage.util import AllowedFileType

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

    Note: Storage operations (upload, download, delete) are handled by
    fides.service.attachment_service.AttachmentService.
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

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "Attachment":
        """Creates a new attachment record in the database."""
        return super().create(db=db, data=data, check_name=check_name)
