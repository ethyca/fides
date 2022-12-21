from typing import Optional

from pydantic import validator

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__NOTIFICATIONS__"


class NotificationSettings(FidesSettings):
    """Configuration settings for data subject and/or data processor notifications"""

    send_request_completion_notification: bool = False
    send_request_receipt_notification: bool = False
    send_request_review_notification: bool = False
    notification_service_type: Optional[str] = None

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

    class Config:
        env_prefix = ENV_PREFIX
