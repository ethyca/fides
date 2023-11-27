from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from fideslang.models import Cookies, PrivacyDeclaration, System
from pydantic import Field
from pydantic.main import BaseModel

from fides.api.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
)
from fides.api.schemas.user import UserResponse


class PrivacyDeclarationResponse(PrivacyDeclaration):
    """Extension of base pydantic model to include DB `id` field in the response"""

    id: str = Field(
        description="The database-assigned ID of the privacy declaration on the system. This is meant to be a read-only field, returned only in API responses"
    )
    cookies: Optional[List[Cookies]] = []


class BasicSystemResponse(System):
    """
    Extension of base pydantic model to include additional fields on the DB model that
    are relevant in API responses.

    This is still meant to be a "lightweight" model that does not reference relationships
    that may require additional querying beyond the `System` db table.
    """

    created_at: datetime


class SystemResponse(BasicSystemResponse):
    """Extension of base pydantic response model to include additional relationship fields that
    may require extra DB queries, like `privacy_declarations`, connection_config fields and cookies.

    This response model is generally useful for an API that returns a detailed view of _single_
    System record. Attempting to return bulk results with this model can lead to n+1 query issues.
    """

    privacy_declarations: Sequence[PrivacyDeclarationResponse] = Field(  # type: ignore[assignment]
        description=PrivacyDeclarationResponse.__doc__,
    )

    connection_configs: Optional[ConnectionConfigurationResponse] = Field(
        description=ConnectionConfigurationResponse.__doc__,
    )

    data_stewards: Optional[List[UserResponse]] = Field(
        description="System managers of the current system",
    )


class SystemHistoryResponse(BaseModel):
    """Response schema for a single system history entry"""

    edited_by: Optional[str]
    system_id: str
    before: Dict[str, Any]
    after: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True
