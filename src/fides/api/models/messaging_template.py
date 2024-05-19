from typing import Any, Dict, List

from fides.api.models.property import Property
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import RelationshipProperty, relationship

from fides.api.db.base_class import Base
from fides.api.schemas.messaging.messaging import MessagingActionType

# Provides default values for initializing the database or replacing deleted values for messaging templates.
# Note: There are additional MessagingActionTypes that are internally used but are not exposed for user customization.
DEFAULT_MESSAGING_TEMPLATES: Dict[str, Any] = {
    MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value: {
        "label": "Subject identity verification",
        "content": {
            "subject": "Your one-time code is {{code}}",
            "body": "Your privacy request verification code is {{code}}. Please return to the Privacy Center and enter the code to continue. This code will expire in {{minutes}} minutes.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_RECEIPT.value: {
        "label": "Privacy request received",
        "content": {
            "subject": "Your privacy request has been received",
            "body": "Your privacy request has been received. We will get back to you shortly.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE.value: {
        "label": "Privacy request approved",
        "content": {
            "subject": "Your privacy request has been approved",
            "body": "Your privacy request has been approved and is currently processing.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY.value: {
        "label": "Privacy request denied",
        "content": {
            "subject": "Your privacy request has been denied",
            "body": "Your privacy request has been denied. {{denial_reason}}.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS.value: {
        "label": "Access request completed",
        "content": {
            "subject": "Your data is ready to be downloaded",
            "body": "Your access request has been completed and can be downloaded at {{download_link}}. For security purposes, this secret link will expire in {{days}} days.",
        },
    },
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION.value: {
        "label": "Erasure request completed",
        "content": {
            "subject": "Your data has been deleted",
            "body": "Your erasure request has been completed.",
        },
    },
}


class MessagingTemplate(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "messaging_template"

    # todo- manually adjust migration to rename key to type, remove unique constraint
    # todo- adjust code that refers to "key", update to use "type"
    type = Column(String, index=True, nullable=False)
    content = Column(MutableDict.as_mutable(JSONB), nullable=False)
    is_enabled = Column(Boolean, default=False, nullable=False)
    properties: RelationshipProperty[List[Property]] = relationship(
        "Property",
        secondary="messaging_template_to_property",
        back_populates="messaging_template",
        lazy="selectin",
    )

    class Config:
        orm_mode = True


