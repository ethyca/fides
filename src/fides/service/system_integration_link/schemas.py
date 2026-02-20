from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from fides.service.system_integration_link.models import SystemConnectionLinkType


class SystemLinkRequest(BaseModel):
    system_fides_key: str
    link_type: SystemConnectionLinkType


class SetSystemLinksRequest(BaseModel):
    links: list[SystemLinkRequest]


class SystemLinkResponse(BaseModel):
    system_fides_key: Optional[str] = None
    system_name: Optional[str] = None
    link_type: SystemConnectionLinkType
    created_at: datetime
