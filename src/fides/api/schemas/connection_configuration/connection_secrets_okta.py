import json
import re
from typing import ClassVar, List, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator

from fides.api.custom_types import AnyHttpUrlStringRemovesSlash
from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)

# Okta domain validation patterns
# Supports: org.okta.com, org.oktapreview.com, org.okta-emea.com
OKTA_DOMAIN_PATTERN = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9\-]*"  # Org name (alphanumeric, can contain hyphens)
    r"(\.[a-zA-Z0-9][a-zA-Z0-9\-]*)*"  # Optional subdomains
    r"\.(okta\.com|oktapreview\.com|okta-emea\.com)$"  # Okta domains
)

# Custom domains must be valid hostnames
CUSTOM_DOMAIN_PATTERN = re.compile(
    r"^[a-zA-Z0-9]"  # Must start with alphanumeric
    r"[a-zA-Z0-9\-\.]*"  # Can contain alphanumeric, hyphens, dots
    r"[a-zA-Z0-9]$"  # Must end with alphanumeric
)


class OktaSchema(ConnectionConfigSecretsSchema):
    """Schema for Okta OAuth2 connection secrets."""

    org_url: AnyHttpUrlStringRemovesSlash = Field(
        title="Organization URL",
        description="The URL of your Okta organization (e.g. https://your-org.okta.com)",
    )
    client_id: str = Field(
        title="OAuth2 Client ID",
        description="The OAuth2 client ID from your Okta service application",
    )
    private_key: str = Field(
        title="Private Key",
        description=(
            "RSA private key in JWK (JSON) format for signing JWT assertions. "
            "Download from Okta: Applications > Your App > Sign On > "
            "Client Credentials > Edit > Generate new key."
        ),
        json_schema_extra={"sensitive": True, "multiline": True},
    )
    scopes: Optional[List[str]] = Field(
        default=["okta.apps.read"],
        title="OAuth2 Scopes",
        description="OAuth2 scopes to request (default: okta.apps.read)",
    )

    _required_components: ClassVar[List[str]] = ["org_url", "client_id", "private_key"]

    @field_validator("org_url")
    @classmethod
    def validate_okta_org_url(cls, value: str) -> str:
        """Validate Okta organization URL.

        Supports standard Okta domains and custom domains:
        - org.okta.com (production)
        - org.oktapreview.com (sandbox/preview)
        - org.okta-emea.com (European instances)
        - Custom domains (enterprise feature)
        """
        parsed = urlparse(str(value))
        hostname = parsed.hostname or parsed.netloc

        if not hostname:
            raise ValueError("Invalid URL: no hostname found")

        # Check if it's a standard Okta domain
        is_okta_domain = OKTA_DOMAIN_PATTERN.match(hostname) is not None

        # If not a standard Okta domain, validate as custom domain
        if not is_okta_domain:
            if not CUSTOM_DOMAIN_PATTERN.match(hostname):
                raise ValueError(
                    f"Invalid Okta domain: {hostname}. "
                    "Expected format: org.okta.com, org.oktapreview.com, "
                    "org.okta-emea.com, or a valid custom domain."
                )

        # Reject admin URLs for standard Okta domains
        if is_okta_domain:
            labels = hostname.split(".")
            if len(labels) >= 3 and labels[-3].endswith("-admin"):
                raise ValueError(
                    "Admin organization URLs (-admin.okta.com) are not supported. "
                    "Use your main organization URL (e.g., https://your-org.okta.com)"
                )

        if parsed.path and parsed.path != "/":
            raise ValueError(
                f"Okta organization URL should not contain a path (got: {parsed.path})"
            )

        return str(value)

    @field_validator("private_key")
    @classmethod
    def validate_private_key_format(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Private key cannot be empty")

        value = value.strip()

        try:
            jwk_dict = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Private key must be in JWK (JSON) format. "
                "Download your key from Okta: Applications > Your App > "
                "Sign On > Client Credentials > Edit > Generate new key"
            ) from exc

        if "d" not in jwk_dict:
            raise ValueError(
                "JWK is not a private key (missing 'd' parameter). "
                "Make sure you're using the private key, not the public key."
            )

        kty = jwk_dict.get("kty")
        if kty not in ("RSA", "EC"):
            raise ValueError(
                f"Unsupported key type: {kty}. Only RSA and EC keys are supported."
            )

        return value


class OktaDocsSchema(OktaSchema, NoValidationSchema):
    """Okta Secrets Schema for API Docs"""
