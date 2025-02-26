from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__NOTIFICATIONS__"


class NotificationSettings(FidesSettings):
    """Configuration settings for Data Subject and/or Data Processor notifications."""

    notification_service_type: Optional[str] = Field(
        default=None,
        description="Sets the notification service type used to send notifications. Accepts mailchimp_transactional, mailgun, twilio_sms, or twilio_email.",
    )
    send_request_completion_notification: bool = Field(
        default=False,
        description="When set to True, enables subject notifications upon privacy request completion.",
    )
    send_request_receipt_notification: bool = Field(
        default=False,
        description="When set to True, enables subject notifications upon privacy request receipt.",
    )
    send_request_review_notification: bool = Field(
        default=False,
        description="When set to True, enables subject notifications upon privacy request review.",
    )
    enable_property_specific_messaging: bool = Field(
        default=False,
        description="When set to True, enables property specific messaging feature, otherwise fall back on the messaging template type env flags set above.",
    )

    @field_validator("notification_service_type", mode="before")
    @classmethod
    def validate_notification_service_type(cls, value: Optional[str]) -> Optional[str]:
        """Ensure the provided type is a valid value."""
        if value:
            valid_values = [
                "mailgun",
                "twilio_text",
                "twilio_email",
                "mailchimp_transactional",
            ]
            value = value.lower()  # force lowercase for safety

            if value not in valid_values:
                raise ValueError(
                    f"Invalid NOTIFICATION_SERVICE_TYPE provided '{value}', must be one of: {', '.join([level for level in valid_values])}"
                )

        return value

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
