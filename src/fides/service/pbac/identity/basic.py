"""BasicIdentityResolver — OSS identity resolution.

Resolves user identities to consumers using:
1. contact_email match
2. scope key match (e.g., email=<identity>)
3. members list match
"""

from __future__ import annotations

from fides.service.pbac.consumers.entities import DataConsumerEntity


class BasicIdentityResolver:
    """Resolve user identities using in-memory consumer data.

    This is the OSS implementation. Consumers are loaded from a
    consumer store (list of DataConsumerEntity) and matched against
    a user identity string.
    """

    def __init__(
        self,
        consumers: list[DataConsumerEntity],
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
        self._by_email: dict[str, DataConsumerEntity] = {}
        self._by_scope_email: dict[str, DataConsumerEntity] = {}
        for c in consumers:
            if c.contact_email:
                self._by_email[c.contact_email] = c
            scope_email = c.scope.get("email")
            if scope_email:
                self._by_scope_email[scope_email] = c

    def resolve(
        self,
        identity: str,
    ) -> DataConsumerEntity | None:
        """Resolve a user identity to a consumer.

        Resolution chain:
        1. Exact match on consumer contact_email
        2. Exact match on consumer scope email
        3. Members list match (identity in consumer's members)
        """
        # 1. contact_email match
        if identity in self._by_email:
            return self._by_email[identity]

        # 2. scope email match
        if identity in self._by_scope_email:
            return self._by_scope_email[identity]

        # 3. members list match
        for consumer in self._consumers:
            if consumer.id and consumer.id in self._members_map:
                if identity in self._members_map[consumer.id]:
                    return consumer

        return None
