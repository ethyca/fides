"""IdentityResolver Protocol — maps user identities to consumers.

OSS provides BasicIdentityResolver (email, external_id, members).
Fidesplus extends with PlatformIdentityResolver (BigQuery IAM, Snowflake RBAC).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from fides.service.pbac.types import ResolvedConsumer


@runtime_checkable
class IdentityResolver(Protocol):
    """Resolve a query user identity to a consumer.

    Resolution should attempt to match the user to a registered
    consumer.  Returns None if the identity cannot be resolved.
    """

    def resolve(
        self,
        user_email: str,
        principal_subject: str | None = None,
    ) -> ResolvedConsumer | None:
        """Resolve a user identity to a consumer.

        Args:
            user_email: Email of the user who ran the query.
            principal_subject: Optional platform-specific principal
                (e.g., BigQuery service account, Snowflake role).

        Returns:
            ResolvedConsumer if matched, None if unresolved.
        """
        ...
