import logging
from typing import Optional

from fides.api.ops.schemas.messaging.messaging import (
    EMAIL_MESSAGING_SERVICES,
    SMS_MESSAGING_SERVICES,
    MessagingMethod,
)

from .fides_settings import FidesSettings

logger = logging.getLogger(__name__)

ENV_PREFIX = "FIDES__NOTIFICATIONS__"


class NotificationSettings(FidesSettings):
    """Configuration settings for data subject and/or data processor notifications"""

    send_request_completion_notification: bool = False
    send_request_receipt_notification: bool = False
    send_request_review_notification: bool = False
    notification_service_type: Optional[str] = None

    def get_messaging_method(self) -> Optional[MessagingMethod]:
        """returns messaging method based on configured notification service type"""
        if self in EMAIL_MESSAGING_SERVICES:
            return MessagingMethod.EMAIL
        if self in SMS_MESSAGING_SERVICES:
            return MessagingMethod.SMS
        return None

    class Config:
        env_prefix = ENV_PREFIX
