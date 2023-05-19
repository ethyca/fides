from typing import List, Optional

from fideslang.models import PrivacyDeclaration, System
from fides.api.ops.schemas.connection_configuration.connection_config import ConnectionConfigurationResponse
from pydantic import Field


class PrivacyDeclarationResponse(PrivacyDeclaration):
    """Extension of base pydantic model to include DB `id` field in the response"""

    id: str = Field(
        description="The database-assigned ID of the privacy declaration on the system. This is meant to be a read-only field, returned only in API responses"
    )


class SystemResponse(System):
    """Extension of base pydantic model to include `privacy_declarations.id` fields in responses"""

    privacy_declarations: List[PrivacyDeclarationResponse] = Field(
        description=PrivacyDeclarationResponse.__doc__,
    )

    connection_config: Optional[ConnectionConfigurationResponse] = Field(
        description=ConnectionConfigurationResponse.__doc__,
    )


