from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import ConfigDict, Field, SerializeAsAny, field_validator, model_validator

from fides.api.custom_types import AnyHttpUrlStringRemovesSlash, URLOriginString
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.messaging.messaging import MessagingServiceType
from fides.config.admin_ui_settings import ErrorNotificationMode


class SqlDryRunMode(str, Enum):
    """SQL dry run mode for controlling execution of SQL statements in privacy requests"""

    none = "none"
    access = "access"
    erasure = "erasure"


class StorageTypeApiAccepted(Enum):
    """Enum for storage destination types accepted in API updates"""

    s3 = "s3"
    gcs = "gcs"
    local = "local"  # local should be used for testing only, not for processing real-world privacy requests


class StorageApplicationConfig(FidesSchema):
    active_default_storage_type: StorageTypeApiAccepted
    model_config = ConfigDict(use_enum_values=True, extra="forbid")


# TODO: the below models classes are "duplicates" of the pydantic
# models that drive the application config. this is to allow every field
# to be optional on the API model, since we want PATCH functionality.
# ideally, we'd not need to duplicate the config modelclasses, and instead
# just make all fields optional by default for the API models.


class NotificationApplicationConfig(FidesSchema):
    """
    API model - configuration settings for data subject and/or data processor notifications
    """

    send_request_completion_notification: Optional[bool] = None
    send_request_receipt_notification: Optional[bool] = None
    send_request_review_notification: Optional[bool] = None
    notification_service_type: Optional[str] = None
    enable_property_specific_messaging: Optional[bool] = None
    model_config = ConfigDict(extra="forbid")

    @field_validator("notification_service_type", mode="before")
    @classmethod
    def validate_notification_service_type(cls, value: Optional[str]) -> Optional[str]:
        """Ensure the provided type is a valid value."""
        if value is None:
            return None  # Allow None values for disabling messaging

        value = value.lower()  # force lowercase for safety
        try:
            MessagingServiceType[value]
        except KeyError:
            raise ValueError(
                f"Invalid notification.notification_service_type provided '{value}', must be one of: {', '.join([service_type.name for service_type in MessagingServiceType])}"
            )

        return value


class ExecutionApplicationConfig(FidesSchema):
    subject_identity_verification_required: Optional[bool] = None
    disable_consent_identity_verification: Optional[bool] = None
    require_manual_request_approval: Optional[bool] = None
    memory_watchdog_enabled: Optional[bool] = None
    sql_dry_run: Optional[SqlDryRunMode] = None

    # Allow deprecated / unknown fields (e.g. “safe_mode”) to pass through
    model_config = ConfigDict(use_enum_values=True, extra="ignore")


class AdminUIConfig(FidesSchema):
    enabled: Optional[bool] = None
    url: SerializeAsAny[Optional[AnyHttpUrlStringRemovesSlash]] = None
    error_notification_mode: Optional[ErrorNotificationMode] = (
        ErrorNotificationMode.CONSOLE_ONLY
    )

    model_config = ConfigDict(extra="forbid")


class PrivacyCenterConfig(FidesSchema):
    url: SerializeAsAny[Optional[AnyHttpUrlStringRemovesSlash]] = None

    model_config = ConfigDict(extra="forbid")


class ConsentConfig(FidesSchema):
    override_vendor_purposes: Optional[bool]
    model_config = ConfigDict(extra="forbid")


class DuplicateDetectionApplicationConfig(FidesSchema):
    """
    API model - configuration settings for duplicate privacy request detection.
    """

    enabled: Optional[bool] = Field(
        default=False,
        description="Whether duplicate detection is enabled. Disabled by default.",
    )

    time_window_days: Optional[int] = Field(
        default=365,
        description="Time window in days for duplicate detection. Default is 1 year.",
        ge=1,
        le=3650,  # Max 10 years
    )

    match_identity_fields: Optional[List[str]] = Field(
        default=["email"],
        description="Identity field names to match on for duplicate detection (e.g., 'email', 'phone_number'). Default is email only.",
    )

    model_config = ConfigDict(extra="forbid")


class SecurityApplicationConfig(FidesSchema):
    # only valid URLs should be set as cors_origins
    # for advanced usage of non-URLs, e.g. wildcards (`*`), the related
    # `cors_origin_regex` property should be used.
    # this is explicitly _not_ accessible via API - it must be used with care.
    cors_origins: SerializeAsAny[Optional[List[URLOriginString]]] = Field(
        default=None,
        description="A list of client addresses allowed to communicate with the Fides webserver.",
    )
    model_config = ConfigDict(extra="forbid")


class ApplicationConfig(FidesSchema):
    """
    Application config settings update body is an arbitrary dict (JSON object)
    We describe it in a schema to enforce some restrictions on the keys passed.

    TODO: Eventually this should be driven by a more formal validation schema for this
    the application config that is properly hooked up to the global pydantic config module.
    """

    storage: Optional[StorageApplicationConfig] = None
    notifications: Optional[NotificationApplicationConfig] = None
    execution: Optional[ExecutionApplicationConfig] = None
    security: Optional[SecurityApplicationConfig] = None
    consent: Optional[ConsentConfig] = None
    admin_ui: Optional[AdminUIConfig] = None
    privacy_center: Optional[PrivacyCenterConfig] = None
    privacy_request_duplicate_detection: Optional[
        DuplicateDetectionApplicationConfig
    ] = None

    @model_validator(mode="before")
    @classmethod
    def validate_not_empty(cls, values: Dict) -> Dict:
        if not values:
            raise ValueError(
                "Config body cannot be empty. DELETE endpoint can be used to null out application config."
            )
        return values

    model_config = ConfigDict(extra="forbid")
