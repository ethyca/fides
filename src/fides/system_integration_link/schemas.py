from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from fides.system_integration_link.entities import SystemIntegrationLinkEntity


class SystemLinkRequest(BaseModel):
    system_fides_key: str


class SetSystemLinksRequest(BaseModel):
    links: list[SystemLinkRequest]


class SystemLinkResponse(BaseModel):
    system_fides_key: str
    system_name: Optional[str] = None
    created_at: datetime

    @classmethod
    def from_entity(cls, entity: SystemIntegrationLinkEntity) -> SystemLinkResponse:
        return cls(
            system_fides_key=entity.system_fides_key,
            system_name=entity.system_name,
            created_at=entity.created_at,
        )
