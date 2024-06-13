from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import RelationshipProperty, Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.property import Property
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


def _link_properties_to_messaging_template(
    db: Session,
    properties: List[Dict[str, Any]],
    messaging_template: MessagingTemplate,
) -> Optional[List[Property]]:
    """
    Link supplied properties to MessagingTemplate and unlink any properties not supplied.
    """
    new_properties = []
    if len(properties) > 0:
        new_properties = (
            db.query(Property)
            .filter(Property.id.in_([prop["id"] for prop in properties]))
            .all()
        )
    messaging_template.properties = new_properties
    messaging_template.save(db)
    return messaging_template.properties


class MessagingTemplate(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "messaging_template"

    type = Column(String, index=True, nullable=False)
    content = Column(MutableDict.as_mutable(JSONB), nullable=False)
    properties: RelationshipProperty[List[Property]] = relationship(
        "Property",
        secondary="messaging_template_to_property",
        back_populates="messaging_templates",
        lazy="selectin",
    )
    is_enabled = Column(Boolean, default=False, nullable=False)

    class Config:
        orm_mode = True

    @classmethod
    def create(
        cls: Type[MessagingTemplate],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> MessagingTemplate:
        """
        Creates a Messaging Template, allows linking properties
        """
        properties = data.pop("properties", [])
        messaging_template: MessagingTemplate = super().create(
            db=db, data=data, check_name=check_name
        )
        # Link Properties to this Messaging Template via the MessagingTemplateToProperty table
        _link_properties_to_messaging_template(db, properties, messaging_template)

        return messaging_template

    def update(self, db: Session, *, data: dict[str, Any]) -> MessagingTemplate:
        """
        Updates a Messaging Template, allows linking properties
        """
        properties = data.pop("properties", [])
        super().update(db=db, data=data)

        # Link Properties to this Messaging Template via the MessagingTemplateToProperty table
        _link_properties_to_messaging_template(db, properties, self)
        return self
