from typing import Dict

from pydantic import BaseModel
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import Base
from fides.api.schemas.messaging.messaging import MessagingActionType

"""
Provides default values for initializing the database or replacing deleted values for messaging templates.
Note: There are additional MessagingActionTypes that are internally used but are not exposed for user customization.
"""
DEFAULT_MESSAGING_TEMPLATES: Dict[str, Dict[str, str]] = {
    MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value: {
        "subject": "Your one-time code is {{code}}",
        "body": "Your privacy request verification code is {{code}}. Please return to the Privacy Center and enter the code to continue. This code will expire in {{minutes}} minutes.",
    },
    MessagingActionType.PRIVACY_REQUEST_RECEIPT.value: {
        "subject": "Your privacy request has been received",
        "body": "Your privacy request has been received. We will get back to you shortly.",
    },
    MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE.value: {
        "subject": "Your privacy request has been approved",
        "body": "Your privacy request has been approved and is currently processing.",
    },
    MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY.value: {
        "subject": "Your privacy request has been denied",
        "body": "Your privacy request has been denied. {{denial_reason}}.",
    },
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS.value: {
        "subject": "Your data is ready to be downloaded",
        "body": "Your access request has been completed and can be downloaded at {{download_link}}. For security purposes, this secret link will expire in {{days}} days.",
    },
    MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION.value: {
        "subject": "Your data has been deleted",
        "body": "Your erasure request has been completed.",
    },
}


class MessagingTemplateBase(BaseModel):
    key: str
    content: Dict[str, str]

    class Config:
        orm_mode = True


class MessagingTemplateRequest(MessagingTemplateBase):
    pass


class MessagingTemplateResponse(MessagingTemplateBase):
    pass


class MessagingTemplate(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "messaging_template"

    key = Column(String, index=True, unique=True, nullable=False)
    content = Column(MutableDict.as_mutable(JSONB), nullable=False)

    class Config:
        orm_mode = True
