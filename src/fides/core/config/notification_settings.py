from typing import Optional

from pydantic import Field, validator

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

    @validator("notification_service_type", pre=True)
    @classmethod
    def validate_notification_service_type(cls, value: Optional[str]) -> Optional[str]:
        """Ensure the provided type is a valid value."""
        if value:
            valid_values = [
                "MAILCHIMP_TRANSACTIONAL",
                "MAILGUN",
                "TWILIO_TEXT",
                "TWILIO_EMAIL",
            ]
            value = value.upper()  # force uppercase for safety

            if value not in valid_values:
                raise ValueError(
                    f"Invalid NOTIFICATION_SERVICE_TYPE provided '{value}', must be one of: {', '.join([level for level in valid_values])}"
                )

        return value

    class Config:
        env_prefix = ENV_PREFIX
