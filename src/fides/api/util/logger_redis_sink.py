from typing import Any, Dict
from fides.api.schemas.privacy_request import PrivacyRequestSource
from loguru._handler import Message  # type: ignore

class RedisLogSink:
    """Custom loguru sink that sends logs to Redis for dataset test privacy requests"""

    def __init__(self) -> None:
        """Initialize the Redis sink."""
        self.cache = None

    def _ensure_cache(self) -> None:
        """Lazily initialize Redis connection when needed."""
        if self.cache is None:
            from fides.api.util.cache import get_cache
            self.cache = get_cache()

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

        # Ensure we have a Redis connection
        self._ensure_cache()

        # Create Redis key using privacy request ID
        key = f"log_{privacy_request_id}"

        # Format log message with additional metadata
        log_entry = {
            "time": record["time"],
            "level": record["level"].name,
            "message": record["message"],
            "extra": dict(record["extra"]),
        }

        # Encode and append log entry to the list in Redis
        self.cache.push_encoded_object(key, log_entry)
