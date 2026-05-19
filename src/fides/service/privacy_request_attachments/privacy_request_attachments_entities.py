"""Domain entities for data-subject-uploaded attachments."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)


@dataclass
class AttachmentUserProvidedRecord:
    """Detach-safe view of an ``attachment_user_provided`` row."""

    id: str
    object_key: str
    storage_key: str
    status: AttachmentUserProvidedStatus
    created_at: datetime
    field_name: str
    property_id: Optional[str]
    policy_key: str

    @classmethod
    def from_orm(cls, obj: AttachmentUserProvided) -> "AttachmentUserProvidedRecord":
        # SA Column descriptors don't narrow to the runtime types declared on
        # this dataclass — ignore arg-type at the two columns that diverge:
        # status (str vs enum) and created_at (Optional vs required).
        return cls(
            id=obj.id,
            object_key=obj.object_key,
            storage_key=obj.storage_key,
            status=obj.status,  # type: ignore[arg-type]
            created_at=obj.created_at,  # type: ignore[arg-type]
            field_name=obj.field_name,
            property_id=obj.property_id,
            policy_key=obj.policy_key,
        )
