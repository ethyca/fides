"""Schema for Microsoft Entra ID (Azure AD) connection secrets.

Uses OAuth 2.0 client credentials flow for Microsoft Graph API access.
"""

import re
from typing import ClassVar, List

from pydantic import Field, field_validator

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)

# Azure tenant ID: 32 hex chars, optionally with hyphens (UUID format)
ENTRA_TENANT_ID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$"
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

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, value: str) -> str:
        """Validate Azure tenant ID format (UUID)."""
        if not value or not value.strip():
            raise ValueError("Tenant ID cannot be empty")
        cleaned = value.strip()
        if not ENTRA_TENANT_ID_PATTERN.match(cleaned):
            raise ValueError(
                "Tenant ID must be a valid Azure AD tenant ID (UUID format). "
                "Find it in Azure Portal: Microsoft Entra ID > Overview > Tenant ID"
            )
        return cleaned

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, value: str) -> str:
        """Validate application (client) ID format (UUID)."""
        if not value or not value.strip():
            raise ValueError("Client ID cannot be empty")
        cleaned = value.strip()
        if not ENTRA_TENANT_ID_PATTERN.match(cleaned):
            raise ValueError(
                "Client ID must be a valid application (client) ID (UUID format). "
                "Find it in Azure Portal: App registrations > Your app > Overview > Application (client) ID"
            )
        return cleaned

    @field_validator("client_secret")
    @classmethod
    def validate_client_secret(cls, value: str) -> str:
        """Ensure client secret is non-empty and is the secret value, not the secret ID."""
        if not value or not value.strip():
            raise ValueError("Client secret cannot be empty")
        cleaned = value.strip()
        if ENTRA_TENANT_ID_PATTERN.match(cleaned):
            raise ValueError(
                "Client secret must be the secret value, not the secret ID. "
                "In Azure Portal: App registrations > Your app > Certificates & secrets: "
                "create or copy the secret's Value (long string), not the Secret ID (GUID)."
            )
        return value


class EntraDocsSchema(EntraSchema, NoValidationSchema):
    """Entra Secrets Schema for API Docs."""
