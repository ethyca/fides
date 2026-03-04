from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fides.system_integration_link.models import (
    SystemConnectionConfigLink,
)


@dataclass
class ConnectionConfigRef:
    """Lightweight reference to a ConnectionConfig (detach-safe)."""

    id: str
    key: str


@dataclass
class SystemRef:
    """Lightweight reference to a System (detach-safe)."""

    id: str
    fides_key: str


@dataclass
class SystemLinkInput:
    """Lightweight input for creating a system-integration link."""

    system_fides_key: str


@dataclass
class SystemIntegrationLinkEntity:
    """Domain entity representing a link between a System and a ConnectionConfig."""

    id: str
    system_id: str
    connection_config_id: str
    created_at: datetime
    updated_at: datetime
    system_fides_key: Optional[str] = None
    system_name: Optional[str] = None

    @classmethod
    def from_orm(
        cls,
        obj: SystemConnectionConfigLink,
        system_fides_key: Optional[str] = None,
        system_name: Optional[str] = None,
    ) -> "SystemIntegrationLinkEntity":
        return cls(
            id=obj.id,
            system_id=obj.system_id,
            connection_config_id=obj.connection_config_id,
            created_at=obj.created_at,  # type: ignore[arg-type]
            updated_at=obj.updated_at,  # type: ignore[arg-type]
            system_fides_key=system_fides_key,
            system_name=system_name,
        )
