from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from fides.api.schemas.base_class import NoValidationSchema


class OAuthGrantType(str, Enum):
    """OAuth2 grant types supported by the system"""

    client_credentials = "client_credentials"


class OAuthConfigSchema(BaseModel):
    """Schema for OAuth2 configuration used in API requests"""

    grant_type: Optional[OAuthGrantType] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = Field(json_schema_extra={"sensitive": True})

    model_config = ConfigDict(
        from_attributes=True, use_enum_values=True, extra="forbid"
    )


class OAuthConfigResponse(BaseModel):
    """Schema for OAuth2 configuration used in API responses with masked sensitive fields"""

    grant_type: OAuthGrantType
    token_url: str
    scope: Optional[str] = None
    client_id: str
    client_secret: str = "**********"  # Always masked in responses

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class OAuthConfigDocsSchema(OAuthConfigSchema, NoValidationSchema):
    """OAuth2 Config Schema for API Docs"""
