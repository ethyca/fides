from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SystemLinkRequest(BaseModel):
    system_fides_key: str


class SetSystemLinksRequest(BaseModel):
    links: list[SystemLinkRequest]


class SystemLinkResponse(BaseModel):
    system_fides_key: str
    system_name: Optional[str] = None
    created_at: datetime
