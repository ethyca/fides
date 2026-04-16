"""IdentityResolver Protocol — maps user identities to consumers.

OSS provides BasicIdentityResolver (email, scope, members).
Fidesplus extends with IdentityGroupProviders (GCP IAM, Google Workspace, Snowflake RBAC).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from fides.service.pbac.consumers.entities import DataConsumerEntity


@runtime_checkable
class IdentityResolver(Protocol):
    """Resolve a query user identity to a consumer.

    Resolution should attempt to match the user to a registered
    consumer. Returns `None` if the identity cannot be resolved.
    """

    def resolve(
        self,
        identity: str,
    ) -> DataConsumerEntity | None:
        """Resolve a user identity to a consumer.

        Args:
            identity: The user who ran the query (email, login name, etc.).

        Returns:
            DataConsumerEntity if matched, None if unresolved.
        """
        ...
