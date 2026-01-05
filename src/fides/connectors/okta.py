"""Module that adds interactions with okta using OAuth2."""

from typing import List, Optional

from fideslang.models import System, SystemMetadata

from fides.api.common_exceptions import ConnectionException
from fides.api.service.connectors.okta_http_client import (
    OktaApplication,
    OktaHttpClient,
)
from fides.connectors.models import (
    ConnectorAuthFailureException,
    ConnectorFailureException,
    OktaConfig,
)


def get_okta_client(okta_config: Optional[OktaConfig]) -> OktaHttpClient:
    """
    Returns an OktaHttpClient for the given okta config using OAuth2 authentication.

    Args:
        okta_config: Configuration with OAuth2 credentials (orgUrl, clientId, privateKey)

    Returns:
        OktaHttpClient instance configured for OAuth2

    Raises:
        ConnectorAuthFailureException: If credentials are missing or invalid
    """
    if not okta_config:
        raise ConnectorAuthFailureException(
            "Okta configuration is required. Please provide orgUrl, clientId, and privateKey."
        )

    try:
        return OktaHttpClient(
            org_url=okta_config.org_url,
            client_id=okta_config.client_id,
            private_key=okta_config.private_key,
            scopes=okta_config.scopes,
        )
    except ConnectionException as e:
        raise ConnectorAuthFailureException(str(e)) from e


def _is_oauth2_auth_error(exc: BaseException) -> bool:
    """Check if the exception chain contains an OAuth2 authentication error."""
    try:
        from requests_oauth2client.exceptions import InvalidClient, UnauthorizedClient

        cause = exc.__cause__
        while cause is not None:
            if isinstance(cause, (InvalidClient, UnauthorizedClient)):
                return True
            cause = cause.__cause__
        return False
    except ImportError:
        # Fallback to string matching if library not available
        error_str = str(exc).lower()
        return "invalid_client" in error_str or "unauthorized" in error_str


def validate_credentials(okta_config: Optional[OktaConfig]) -> None:
    """
    Validates okta credentials by attempting to list applications with limit of 1.

    Args:
        okta_config: Configuration with OAuth2 credentials

    Raises:
        ConnectorAuthFailureException: If authentication fails
        ConnectorFailureException: If the API request fails for other reasons
    """
    try:
        client = get_okta_client(okta_config=okta_config)
        client.list_applications(limit=1)
    except ConnectionException as e:
        if _is_oauth2_auth_error(e):
            raise ConnectorAuthFailureException(
                "Authentication failed. Please verify your OAuth2 credentials."
            ) from e
        raise ConnectorFailureException(f"Okta API error: {e}") from e


def list_okta_applications(okta_client: OktaHttpClient) -> List[OktaApplication]:
    """
    Returns a list of Okta applications using pagination.

    Args:
        okta_client: Configured OktaHttpClient instance

    Returns:
        List of OktaApplication objects from Okta API

    Raises:
        ConnectorFailureException: If the API request fails
    """
    try:
        return okta_client.list_all_applications()
    except ConnectionException as e:
        raise ConnectorFailureException(f"Failed to list Okta applications: {e}") from e


def create_okta_systems(
    okta_applications: List[OktaApplication], organization_key: str
) -> List[System]:
    """
    Returns a list of system objects given a list of Okta applications.

    Only includes ACTIVE applications.

    Args:
        okta_applications: List of OktaApplication dicts from Okta API.
            Note: OktaApplication is a TypedDict (dict at runtime with type hints),
            not a Pydantic model, so dict-style access with .get() is used.
        organization_key: The organization fides_key to associate with systems

    Returns:
        List of System objects for active Okta applications
    """
    systems = [
        System(
            fides_key=app.get("id", ""),
            name=app.get("name", ""),
            fidesctl_meta=SystemMetadata(
                resource_id=app.get("id", ""),
            ),
            description=f"Fides Generated Description for Okta Application: {app.get('label', app.get('name', 'Unknown'))}",
            system_type="okta_application",
            organization_fides_key=organization_key,
            privacy_declarations=[],
        )
        for app in okta_applications
        if app.get("status") == "ACTIVE"
    ]
    return systems
