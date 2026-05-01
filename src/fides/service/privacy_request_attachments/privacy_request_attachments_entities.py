"""Domain entities for data-subject-uploaded attachments."""

from dataclasses import dataclass
from datetime import datetime

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
    property_id: str
    policy_key: str

    @classmethod
    def from_orm(cls, obj: AttachmentUserProvided) -> "AttachmentUserProvidedRecord":
        return cls(
            id=obj.id,
            object_key=obj.object_key,  # type: ignore[arg-type]
            storage_key=obj.storage_key,  # type: ignore[arg-type]
            status=obj.status,  # type: ignore[arg-type]
            created_at=obj.created_at,  # type: ignore[arg-type]
            field_name=obj.field_name,  # type: ignore[arg-type]
            property_id=obj.property_id,  # type: ignore[arg-type]
            policy_key=obj.policy_key,  # type: ignore[arg-type]
        )
