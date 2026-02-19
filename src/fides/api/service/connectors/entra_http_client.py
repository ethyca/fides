"""HTTP client for Microsoft Graph API using OAuth 2.0 client credentials.

Used by the Entra connector for IDP discovery (list service principals).
"""

from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from fides.api.common_exceptions import ConnectionException

GRAPH_BASE_URL = "https://graph.microsoft.com"
GRAPH_DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
DEFAULT_REQUEST_TIMEOUT = 30
# Max page size for servicePrincipals list (Microsoft Graph limit)
SERVICE_PRINCIPALS_PAGE_SIZE = 100
# Minimal $select for connection test and list
SERVICE_PRINCIPALS_SELECT = (
    "id,displayName,appDisplayName,accountEnabled,createdDateTime,"
    "preferredSingleSignOnMode,servicePrincipalType,appId,description"
)


class EntraHttpClient:
    """
    HTTP client for Microsoft Graph with client credentials flow.

    - Obtains access token from login.microsoftonline.com
    - Calls Graph API (e.g. list service principals) with Bearer token
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
        return (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        )

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

    def list_service_principals(
        self,
        top: int = SERVICE_PRINCIPALS_PAGE_SIZE,
        next_link: Optional[str] = None,
        select: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List service principals (enterprise applications) from Microsoft Graph.

        Args:
            top: Page size (max 100 for this endpoint).
            next_link: If provided, GET this URL instead of building one (pagination).
            select: OData $select string; default is minimal fields for IDP monitor.

        Returns:
            Tuple of (list of service principal dicts, next_link or None).
        """
        token = self._get_token()
        select = select or SERVICE_PRINCIPALS_SELECT
        if next_link:
            url = next_link
        else:
            url = (
                f"{GRAPH_BASE_URL}/v1.0/servicePrincipals"
                f"?$top={min(top, SERVICE_PRINCIPALS_PAGE_SIZE)}"
                f"&$select={select}"
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
                            "add application permission 'Application.Read.All' (Microsoft Graph), "
                            "then grant admin consent."
                        )
                except (ValueError, KeyError, TypeError):
                    pass
            raise ConnectionException(msg)
        data = response.json()
        value = data.get("value", [])
        if not isinstance(value, list):
            value = []
        next_link_out = data.get("@odata.nextLink")
        return value, next_link_out
