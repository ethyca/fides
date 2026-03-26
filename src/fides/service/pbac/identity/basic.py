"""BasicIdentityResolver — OSS identity resolution.

Resolves user identities to consumers using:
1. contact_email match
2. external_id match
3. members list match
"""

from __future__ import annotations

from fides.service.pbac.types import ResolvedConsumer


class BasicIdentityResolver:
    """Resolve user identities using in-memory consumer data.

    This is the OSS implementation. Consumers are loaded from a
    consumer store (list of ResolvedConsumer) and matched against
    user email or principal subject.

    Fidesplus extends this with PlatformIdentityResolver that queries
    BigQuery IAM / Snowflake RBAC before falling back to this chain.
    """

    def __init__(
        self,
        consumers: list[ResolvedConsumer],
        members_map: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize with a list of consumers.

        Args:
            consumers: All registered consumers.
            members_map: Optional mapping of consumer ID -> member emails.
                Used for group membership resolution.
        """
        self._consumers = consumers
        self._members_map = members_map or {}

        # Build indexes for fast lookup
        self._by_email: dict[str, ResolvedConsumer] = {}
        self._by_external_id: dict[str, ResolvedConsumer] = {}
        for c in consumers:
            if c.email:
                self._by_email[c.email] = c
            if c.external_id:
                self._by_external_id[c.external_id] = c

    def resolve(
        self,
        user_email: str,
        principal_subject: str | None = None,
    ) -> ResolvedConsumer | None:
        """Resolve a user identity to a consumer.

        Resolution chain:
        1. Exact match on consumer contact_email
        2. Exact match on consumer external_id
        3. Members list match (user email in consumer's members)
        """
        # 1. contact_email match
        if user_email in self._by_email:
            return self._by_email[user_email]

        # 2. external_id match (try principal_subject first, then email)
        if principal_subject and principal_subject in self._by_external_id:
            return self._by_external_id[principal_subject]
        if user_email in self._by_external_id:
            return self._by_external_id[user_email]

        # 3. members list match
        for consumer in self._consumers:
            if consumer.id and consumer.id in self._members_map:
                if user_email in self._members_map[consumer.id]:
                    return consumer

        return None
