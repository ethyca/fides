from __future__ import annotations

from typing import Dict, Optional

from pydantic import Extra, root_validator, validator

from fides.api.ops.schemas.storage.storage import StorageType
from fides.lib.schemas.base_class import BaseSchema


class StorageApplicationConfig(BaseSchema):
    active_default_storage_type: StorageType

    class Config:
        use_enum_values = True
        extra = Extra.forbid

    @validator("active_default_storage_type")
    @classmethod
    def validate_storage_type(cls, storage_type: StorageType) -> StorageType:
        """
        For now, only `local` and `s3` storage types are supported
        as an `active_default_storage_type`
        """
        valid_storage_types = (StorageType.local.value, StorageType.s3.value)
        if storage_type not in valid_storage_types:
            raise ValueError(
                f"Only '{valid_storage_types}' are supported as `active_default_storage_type`s"
            )
        return storage_type


# TODO: the below models classes are "duplicates" of the pydantic
# models that drive the application config. this is to allow every field
# to be optional on the API model, since we want PATCH functionality.
# ideally, we'd not need to duplicate the config modelclasses, and instead
# just make all fields optional by default for the API models.


class NotificationApplicationConfig(BaseSchema):
    """
    API model - configuration settings for data subject and/or data processor notifications
    """

    send_request_completion_notification: Optional[bool]
    send_request_receipt_notification: Optional[bool]
    send_request_review_notification: Optional[bool]
    notification_service_type: Optional[str]

    @validator("notification_service_type", pre=True)
    @classmethod
    def validate_notification_service_type(cls, value: Optional[str]) -> Optional[str]:
        """Ensure the provided type is a valid value."""
        if value:
            valid_values = ["MAILGUN", "TWILIO_TEXT", "TWILIO_EMAIL"]
            value = value.upper()  # force uppercase for safety

            if value not in valid_values:
                raise ValueError(
                    f"Invalid NOTIFICATION_SERVICE_TYPE provided '{value}', must be one of: {', '.join([level for level in valid_values])}"
                )

        return value


class ExecutionApplicationConfig(BaseSchema):
    subject_identity_verification_required: bool

    class Config:
        extra = Extra.forbid


class ApplicationConfig(BaseSchema):
    """
    Application config settings update body is an arbitrary dict (JSON object)
    We describe it in a schema to enforce some restrictions on the keys passed.

    TODO: Eventually this should be driven by a more formal validation schema for this
    the application config that is properly hooked up to the global pydantic config module.
    """

    storage: Optional[StorageApplicationConfig]
    notifications: Optional[NotificationApplicationConfig]
    execution: Optional[ExecutionApplicationConfig]

    @root_validator(pre=True)
    def validate_not_empty(cls, values: Dict) -> Dict:
        if not values:
            raise ValueError("Config body cannot be empty!")
        return values

    class Config:
        extra = Extra.forbid
