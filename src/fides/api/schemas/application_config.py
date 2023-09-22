from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import Extra, Field, root_validator, validator

from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.messaging.messaging import MessagingServiceType


class StorageTypeApiAccepted(Enum):
    """Enum for storage destination types accepted in API updates"""

    s3 = "s3"
    local = "local"  # local should be used for testing only, not for processing real-world privacy requests


class StorageApplicationConfig(FidesSchema):
    active_default_storage_type: StorageTypeApiAccepted

    class Config:
        use_enum_values = True
        extra = Extra.forbid


# TODO: the below models classes are "duplicates" of the pydantic
# models that drive the application config. this is to allow every field
# to be optional on the API model, since we want PATCH functionality.
# ideally, we'd not need to duplicate the config modelclasses, and instead
# just make all fields optional by default for the API models.


class NotificationApplicationConfig(FidesSchema):
    """
    API model - configuration settings for data subject and/or data processor notifications
    """

    send_request_completion_notification: Optional[bool]
    send_request_receipt_notification: Optional[bool]
    send_request_review_notification: Optional[bool]
    notification_service_type: Optional[str]

    class Config:
        extra = Extra.forbid

    @validator("notification_service_type", pre=True)
    @classmethod
    def validate_notification_service_type(cls, value: str) -> Optional[str]:
        """Ensure the provided type is a valid value."""
        value = value.lower()  # force lowercase for safety
        try:
            MessagingServiceType[value]
        except KeyError:
            raise ValueError(
                f"Invalid notification.notification_service_type provided '{value}', must be one of: {', '.join([service_type.name for service_type in MessagingServiceType])}"
            )

        return value


class ExecutionApplicationConfig(FidesSchema):
    subject_identity_verification_required: Optional[bool]
    require_manual_request_approval: Optional[bool]

    class Config:
        extra = Extra.forbid


class SecurityApplicationConfig(FidesSchema):
    cors_origins: Optional[List[str]] = Field(
        default=None,
        description="A list of client addresses allowed to communicate with the Fides webserver.",
    )

    class Config:
        extra = Extra.forbid


class ApplicationConfig(FidesSchema):
    """
    Application config settings update body is an arbitrary dict (JSON object)
    We describe it in a schema to enforce some restrictions on the keys passed.

    TODO: Eventually this should be driven by a more formal validation schema for this
    the application config that is properly hooked up to the global pydantic config module.
    """

    storage: Optional[StorageApplicationConfig]
    notifications: Optional[NotificationApplicationConfig]
    execution: Optional[ExecutionApplicationConfig]
    security: Optional[SecurityApplicationConfig]

    @root_validator(pre=True)
    def validate_not_empty(cls, values: Dict) -> Dict:
        if not values:
            raise ValueError(
                "Config body cannot be empty. DELETE endpoint can be used to null out application config."
            )
        return values

    class Config:
        extra = Extra.forbid
