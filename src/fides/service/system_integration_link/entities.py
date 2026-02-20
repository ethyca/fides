from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fides.service.system_integration_link.models import (
    SystemConnectionConfigLink,
    SystemConnectionLinkType,
)


@dataclass
class SystemIntegrationLinkEntity:
    """Domain entity representing a link between a System and a ConnectionConfig."""

    id: str
    system_id: str
    connection_config_id: str
    link_type: SystemConnectionLinkType
    created_at: datetime
    updated_at: datetime
    system_fides_key: Optional[str] = None
    system_name: Optional[str] = None

    @classmethod
    def from_orm(cls, obj: SystemConnectionConfigLink) -> "SystemIntegrationLinkEntity":
        system = obj.system
        return cls(
            id=obj.id,
            system_id=obj.system_id,
            connection_config_id=obj.connection_config_id,
            link_type=obj.link_type,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            system_fides_key=system.fides_key if system else None,
            system_name=system.name if system else None,
        )
