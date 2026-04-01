"""Redis-backed identity resolution for query log entries."""

from __future__ import annotations

from loguru import logger

from fides.service.pbac.consumers.entities import DataConsumerEntity
from fides.service.pbac.consumers.repository import DataConsumerRedisRepository


class RedisIdentityResolver:
    """Resolve a query log user identity to a DataConsumer.

    Resolution chain:
    1. Exact match on DataConsumer.contact_email
    2. Match on DataConsumer.external_id (for group/project consumers)

    Returns None if the identity cannot be resolved (recorded as a gap).
    """

    def __init__(self, consumer_repo: DataConsumerRedisRepository) -> None:
        self._consumer_repo = consumer_repo

    def resolve(
        self,
        identity: str,
    ) -> DataConsumerEntity | None:
        """Attempt to resolve a user identity to a DataConsumer."""
        matches = self._consumer_repo.get_by_index("contact_email", identity)
        if matches:
            return matches[0]

        matches = self._consumer_repo.get_by_index("external_id", identity)
        if matches:
            return matches[0]

        logger.debug("Could not resolve identity for user={}", identity)
        return None
