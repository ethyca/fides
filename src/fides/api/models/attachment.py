from enum import Enum as EnumType
from typing import IO, TYPE_CHECKING, Any, Tuple
from io import BytesIO

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func, orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.service.storage.util import AllowedFileType

if TYPE_CHECKING:
    pass  # Will add imports if needed

# Import GCS client function for backward compatibility with tests
from fides.api.service.storage.gcs import get_gcs_client


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
    Persisting the attachment to storage is handled by AttachmentService.
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
        try:
            file_extension = self.file_name.split(".")[-1]
            return AllowedFileType[file_extension].value
        except KeyError:
            raise ValueError(f"Invalid or unallowed file extension: {self.file_name}")

    @property
    def file_key(self) -> str:
        """Returns the file key of the attachment."""
        return f"{self.id}/{self.file_name}"

    def delete_from_db_only(self, db: Session) -> None:
        """Deletes only the attachment record from the database. Storage operations should be handled separately."""
        # Delete all references to the attachment
        for reference in self.references:
            reference.delete(db)
        super().delete(db=db)

    def delete(self, db: Session) -> None:
        """
        Backward compatibility method for tests.
        Deletes attachment from both storage and database using AttachmentService.
        """
        # Import here to avoid circular imports
        from fides.service.attachment import AttachmentService

        attachment_service = AttachmentService(db)
        attachment_service.delete_completely(self)

    @classmethod
    def create_and_upload(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        attachment_file: IO[bytes],
        check_name: bool = False,
    ) -> "Attachment":
        """
        Backward compatibility method for tests.
        Creates attachment record and uploads file using AttachmentService.
        """
        # Import here to avoid circular imports
        from fides.service.attachment import AttachmentService

        attachment_service = AttachmentService(db)
        return attachment_service.create_and_upload(
            attachment_data=data,
            attachment_file=attachment_file,
            references=None,  # No references in old interface
        )

    @staticmethod
    def delete_attachments_for_reference_and_type(
        db: Session, reference_id: str, reference_type: AttachmentReferenceType
    ) -> None:
        """
        Backward compatibility method for tests.
        Deletes all attachment records and files from storage for given reference.
        """
        # Import here to avoid circular imports
        from fides.service.attachment import AttachmentService

        AttachmentService.delete_attachments_for_reference_and_type(
            db, reference_id, reference_type
        )

    def retrieve_attachment(self) -> Tuple[int, str]:
        """
        Backward compatibility method for tests.
        Returns attachment size and download URL using AttachmentService.
        """
        # Import here to avoid circular imports
        from fides.service.attachment import AttachmentService
        from fides.api.api.deps import get_autoclose_db_session

        with get_autoclose_db_session() as session:
            attachment_service = AttachmentService(session)
            return attachment_service.get_download_info(self)

    def retrieve_attachment_content(self) -> Tuple[int, BytesIO]:
        """
        Backward compatibility method for tests.
        Returns attachment size and content using AttachmentService.
        """
        # Import here to avoid circular imports
        from fides.service.attachment import AttachmentService
        from fides.api.api.deps import get_autoclose_db_session

        with get_autoclose_db_session() as session:
            attachment_service = AttachmentService(session)
            return attachment_service.get_content(self)

    def delete_attachment_from_storage(self) -> None:
        """
        Backward compatibility method for tests.
        Deletes attachment from storage only (keeps database record) using AttachmentService.
        """
        # Import here to avoid circular imports
        from fides.service.attachment import AttachmentService
        from fides.api.api.deps import get_autoclose_db_session

        with get_autoclose_db_session() as session:
            attachment_service = AttachmentService(session)
            attachment_service._delete_from_storage(self)
