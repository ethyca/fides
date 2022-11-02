import logging

from .fides_settings import FidesSettings

logger = logging.getLogger(__name__)

ENV_PREFIX = "FIDES__NOTIFICATIONS__"


class NotificationSettings(FidesSettings):
    """Configuration settings for data subject and/or data processor notifications"""

    send_request_completion_notification: bool = False
    send_request_receipt_notification: bool = False
    send_request_review_notification: bool = False

    class Config:
        env_prefix = ENV_PREFIX
