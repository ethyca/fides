from typing import TYPE_CHECKING, Any, Dict
from fides.api.schemas.privacy_request import PrivacyRequestSource
from loguru._handler import Message  # type: ignore

if TYPE_CHECKING:
    from fides.api.util.cache import FidesopsRedis

class RedisLogSink:
    """Custom loguru sink that sends logs to Redis for dataset test privacy requests"""

    def __init__(self, redis_connection: "FidesopsRedis") -> None:
        """Initialize the Redis sink with a Redis connection.

        Args:
            redis_connection: A FidesopsRedis instance
        """
        self.cache = redis_connection

    def __call__(self, message: Message) -> None:
        """Write log message to Redis if conditions are met.
        This method signature matches Loguru's sink interface."""
        record: Dict[str, Any] = message.record

        # Extract privacy request context
        extras = record["extra"]
        privacy_request_id = extras.get("privacy_request_id")
        privacy_request_source = extras.get("privacy_request_source")

        # Only process logs with privacy request ID and source is dataset_test
        if (
            not privacy_request_id
            or privacy_request_source != PrivacyRequestSource.dataset_test.value
        ):
            return

        # Create Redis key using privacy request ID
        key = f"log_{privacy_request_id}"

        # Format log message
        log_entry = {
            "time": record["time"],
            "level": record["level"].name,
            "message": record["message"],
            "extra": dict(record["extra"]),
        }

        # Encode and append log entry to the list in Redis
        self.cache.rpush_encoded_object(key, log_entry)
