"""Identity and dataset resolution for query log entries.

Maps platform-specific identifiers (emails, table references) to Fides
domain entities (DataConsumer, Dataset).
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from fides.api.util.cache import get_cache
from fides.service.pbac.consumers.entities import DataConsumerEntity
from fides.service.pbac.consumers.repository import DataConsumerRedisRepository
from fides.service.pbac.purposes.repository import DataPurposeRedisRepository
from fides.service.pbac.types import TableRef


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
        user_email: str,
        principal_subject: str | None = None,
    ) -> Optional[DataConsumerEntity]:
        """Attempt to resolve a user identity to a DataConsumer."""

        # Strategy 1: match by contact_email
        matches = self._consumer_repo.get_by_index("contact_email", user_email)
        if matches:
            return matches[0]

        # Strategy 2: match by external_id (e.g., "user:email@example.com")
        if principal_subject:
            matches = self._consumer_repo.get_by_index("external_id", principal_subject)
            if matches:
                return matches[0]

        # Also try the email as external_id
        matches = self._consumer_repo.get_by_index("external_id", user_email)
        if matches:
            return matches[0]

        logger.debug(
            "Could not resolve identity for user_email={}, principal_subject={}",
            user_email,
            principal_subject,
        )
        return None


class DatasetResolver:
    """Resolve platform table references to Fides dataset fides_keys.

    Uses a configurable mapping strategy:
    - Direct match: ``{dataset}.{table}`` → Fides dataset ``fides_key``
    - Qualified match: ``{project}.{dataset}.{table}`` → Fides dataset
    - Custom prefix mapping (e.g., strip project prefix)
    """

    def __init__(
        self,
        dataset_mappings: Optional[dict[str, str]] = None,
    ) -> None:
        # qualified_name -> fides_key
        self._mappings: dict[str, str] = dataset_mappings or {}

    def resolve(self, table_ref: TableRef) -> str | None:
        """Resolve a table reference to a Fides dataset fides_key.

        Returns None if no mapping is found.
        """
        # Try full qualified name first
        if table_ref.qualified_name in self._mappings:
            return self._mappings[table_ref.qualified_name]

        # Try dataset.table (without project)
        short_name = f"{table_ref.dataset}.{table_ref.table}"
        if short_name in self._mappings:
            return self._mappings[short_name]

        # Try just the dataset name as fides_key
        if table_ref.dataset in self._mappings:
            return self._mappings[table_ref.dataset]

        # Fall back to using the dataset name directly as fides_key
        return table_ref.dataset

    def add_mapping(self, platform_ref: str, fides_key: str) -> None:
        """Add a table reference → fides_key mapping."""
        self._mappings[platform_ref] = fides_key


def build_identity_resolver(
    purpose_repo: DataPurposeRedisRepository,
) -> RedisIdentityResolver:
    """Factory to create a RedisIdentityResolver with proper dependencies."""
    cache = get_cache()
    consumer_repo = DataConsumerRedisRepository(cache, purpose_repo)
    return RedisIdentityResolver(consumer_repo)
