"""Schema for Microsoft Entra ID (Azure AD) connection secrets.

Uses OAuth 2.0 client credentials flow for Microsoft Graph API access.
"""

from typing import ClassVar, List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class EntraSchema(ConnectionConfigSecretsSchema):
    """Schema for Microsoft Entra ID (Azure AD) OAuth2 client credentials."""

    tenant_id: str = Field(
        title="Tenant ID",
        description="Azure AD tenant ID (directory ID) from the Azure portal",
    )
    client_id: str = Field(
        title="Client ID",
        description="Application (client) ID from your Entra app registration",
    )
    client_secret: str = Field(
        title="Client Secret",
        description="Client secret value from your Entra app registration (Certificates & secrets)",
        json_schema_extra={"sensitive": True},
    )

    _required_components: ClassVar[List[str]] = [
        "tenant_id",
        "client_id",
        "client_secret",
    ]


class EntraDocsSchema(EntraSchema, NoValidationSchema):
    """Entra Secrets Schema for API Docs."""
