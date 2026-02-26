"""HTTP client for Microsoft Graph API using OAuth 2.0 client credentials.

Used by the Entra connector for IDP discovery (list app registrations).
"""

from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from fides.api.common_exceptions import ConnectionException

GRAPH_BASE_URL = "https://graph.microsoft.com"
GRAPH_DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
DEFAULT_REQUEST_TIMEOUT = 30

# /v1.0/applications — app registrations (max $top=999)
APPLICATIONS_PAGE_SIZE = 999
APPLICATIONS_SELECT = "id,displayName,appId,createdDateTime,description,signInAudience"

# /v1.0/servicePrincipals — enterprise apps / service principals (max $top=100)
SERVICE_PRINCIPALS_PAGE_SIZE = 100
SERVICE_PRINCIPALS_SELECT = (
    "id,displayName,appDisplayName,accountEnabled,createdDateTime,"
    "preferredSingleSignOnMode,servicePrincipalType,appId,description"
)


class EntraHttpClient:
    """
    HTTP client for Microsoft Graph with client credentials flow.

    - Obtains access token from login.microsoftonline.com
    - Calls Graph API (e.g. list app registrations) with Bearer token
    - Supports pagination via @odata.nextLink
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        *,
        session: Optional[requests.Session] = None,
    ):
        self.tenant_id = tenant_id.strip()
        self.client_id = client_id.strip()
        self.client_secret = client_secret
        self._token: Optional[str] = None
        if session is not None:
            self._session = session
        else:
            self._session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=(429, 500, 502, 503, 504),
            )
            self._session.mount("https://", HTTPAdapter(max_retries=retries))

    def _token_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

    def _get_token(self) -> str:
        """Obtain OAuth2 access token via client credentials grant."""
        if self._token:
            return self._token
        response = self._session.post(
            self._token_url(),
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": GRAPH_DEFAULT_SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
        if not response.ok:
            msg = (
                f"Failed to obtain Entra access token: {response.status_code}. "
                "Verify tenant ID, client ID, and client secret."
            )
            try:
                body = response.json()
                if "error_description" in body:
                    msg = f"{msg} {body['error_description']}"
            except (ValueError, KeyError):
                pass
            raise ConnectionException(msg)
        data = response.json()
        self._token = data.get("access_token")
        if not self._token:
            raise ConnectionException("Entra token response missing access_token")
        return self._token

    def _list_graph_collection(
        self,
        resource_path: str,
        top: int,
        max_top: int,
        default_select: str,
        next_link: Optional[str],
        select: Optional[str],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Shared pagination helper for Microsoft Graph list endpoints.

        Builds the initial URL from resource_path / top / select, or uses next_link
        directly when continuing a paginated result set. Handles 401 token invalidation
        and surfaces a friendly 403 message for missing API permissions.
        """
        token = self._get_token()
        resolved_select = select or default_select
        if next_link:
            url = next_link
        else:
            url = (
                f"{GRAPH_BASE_URL}{resource_path}"
                f"?$top={min(top, max_top)}"
                f"&$select={resolved_select}"
            )
        response = self._session.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
        if not response.ok:
            if response.status_code == 401:
                self._token = None
            msg = f"Microsoft Graph request failed: {response.status_code}. {response.text[:200]}"
            if response.status_code == 403:
                try:
                    body = response.json()
                    err = body.get("error", {})
                    if err.get("code") == "Authorization_RequestDenied":
                        msg = (
                            "Insufficient Microsoft Graph permissions. "
                            "In Azure Portal: App registrations > Your app > API permissions: "
                            "add the required application permission (Microsoft Graph), "
                            "then grant admin consent."
                        )
                except (ValueError, KeyError, TypeError):
                    pass
            raise ConnectionException(msg)
        data = response.json()
        value = data.get("value", [])
        if not isinstance(value, list):
            value = []
        return value, data.get("@odata.nextLink")

    def list_applications(
        self,
        top: int = APPLICATIONS_PAGE_SIZE,
        next_link: Optional[str] = None,
        select: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List app registrations (/v1.0/applications) from Microsoft Graph.

        Requires the 'Application.Read.All' application permission with admin consent.

        Args:
            top: Page size (max 999).
            next_link: If provided, resumes pagination from this URL.
            select: Comma-separated OData $select fields. When omitted, a minimal
                    default set is used. Callers can supply a custom list, e.g.
                    "id,displayName,appId,createdDateTime,web,requiredResourceAccess".

        Returns:
            Tuple of (list of application dicts, next_link or None).
        """
        return self._list_graph_collection(
            resource_path="/v1.0/applications",
            top=top,
            max_top=APPLICATIONS_PAGE_SIZE,
            default_select=APPLICATIONS_SELECT,
            next_link=next_link,
            select=select,
        )

    def list_service_principals(
        self,
        top: int = SERVICE_PRINCIPALS_PAGE_SIZE,
        next_link: Optional[str] = None,
        select: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List service principals (/v1.0/servicePrincipals) from Microsoft Graph.

        Useful for reading fields only available on the service principal object
        (e.g. preferredSingleSignOnMode, accountEnabled, servicePrincipalType).
        Requires the 'Application.Read.All' application permission with admin consent.

        Args:
            top: Page size (max 100 for this endpoint).
            next_link: If provided, resumes pagination from this URL.
            select: Comma-separated OData $select fields. When omitted, a minimal
                    default set is used. Callers can supply a custom list, e.g.
                    "id,displayName,appId,accountEnabled,preferredSingleSignOnMode".

        Returns:
            Tuple of (list of service principal dicts, next_link or None).
        """
        return self._list_graph_collection(
            resource_path="/v1.0/servicePrincipals",
            top=top,
            max_top=SERVICE_PRINCIPALS_PAGE_SIZE,
            default_select=SERVICE_PRINCIPALS_SELECT,
            next_link=next_link,
            select=select,
        )
