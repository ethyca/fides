import json
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import requests
from requests.auth import AuthBase
from typing_extensions import TypedDict

from fides.api.common_exceptions import ConnectionException

if TYPE_CHECKING:
    from requests_oauth2client import DPoPKey, OAuth2Client


class _JwkBase(TypedDict, total=False):
    """Base JWK fields (all optional)."""

    kty: str  # Key type: "RSA" or "EC"
    alg: str  # Algorithm: RS256, ES256, etc.
    # EC-specific
    crv: str  # Curve: P-256, P-384, P-521
    x: str
    y: str
    # RSA-specific
    n: str  # Modulus
    e: str  # Public exponent


class PrivateJwk(_JwkBase):
    """JWK private key structure per RFC 7517."""

    d: str


class OktaApplication(TypedDict, total=False):
    """Okta Application object from the API."""

    id: str
    name: str
    label: str
    status: str  # ACTIVE, INACTIVE, DELETED
    created: str
    lastUpdated: str
    signOnMode: str


DEFAULT_OKTA_SCOPES = ("okta.apps.read",)
DEFAULT_API_LIMIT = 200
DEFAULT_MAX_PAGES = 100
DEFAULT_REQUEST_TIMEOUT = 30

EC_CURVE_ALG_MAP = {
    "P-256": "ES256",
    "P-384": "ES384",
    "P-521": "ES512",
}


class OktaHttpClient:
    """
    HTTP client for Okta API with OAuth2 private_key_jwt + DPoP.

    Uses custom implementation instead of Okta SDK because the SDK lacks DPoP support.
    """

    def __init__(
        self,
        org_url: str,
        client_id: str,
        private_key: Union[str, PrivateJwk],
        scopes: Optional[List[str]] = None,
        *,
        oauth_client: "Optional[OAuth2Client]" = None,  # For test injection
        dpop_key: "Optional[DPoPKey]" = None,  # For test injection
    ):
        self.org_url = org_url.rstrip("/")
        self.scopes = tuple(scopes) if scopes is not None else DEFAULT_OKTA_SCOPES

        if oauth_client is not None or dpop_key is not None:
            if oauth_client is None or dpop_key is None:
                raise ValueError(
                    "Both oauth_client and dpop_key must be provided when injecting test dependencies."
                )
            self._oauth_client = oauth_client
            self._dpop_key = dpop_key
            return

        try:
            from requests_oauth2client import DPoPKey, OAuth2Client, PrivateKeyJwt

            private_jwk = self._parse_jwk(private_key)
            alg = self._determine_alg_from_jwk(private_jwk)

            # DPoP (RFC 9449) requires a separate key from client authentication.
            # ES256 is used regardless of the client auth key type because:
            # 1. It's explicitly recommended by RFC 9449 for DPoP proofs
            # 2. It provides strong security with compact signatures
            # 3. Okta supports ES256 for DPoP across all configurations
            self._dpop_key = DPoPKey.generate(alg="ES256")

            self._oauth_client = OAuth2Client(
                token_endpoint=f"{self.org_url}/oauth2/v1/token",
                auth=PrivateKeyJwt(client_id, private_jwk, alg=alg),
            )
        except ImportError as e:
            raise ConnectionException(
                "The 'requests-oauth2client' library is required for Okta connector. "
                "Please install it with: pip install requests-oauth2client"
            ) from e
        except (ValueError, TypeError) as e:
            # Generic message avoids leaking key content
            raise ConnectionException(
                "Invalid private key format. Ensure the key is a valid JWK with 'd' parameter."
            ) from e

    @staticmethod
    def _parse_jwk(private_key: Union[str, PrivateJwk]) -> PrivateJwk:
        """Parse private key from string or dict.

        Note: Full validation (kty, 'd' param) is done by OktaSchema.
        This method handles string→dict conversion for already-validated secrets.

        Args:
            private_key: JWK as either a JSON string or dict

        Returns:
            Parsed JWK dictionary

        Raises:
            ValueError: If key is not valid JSON
        """
        if isinstance(private_key, dict):
            return private_key

        try:
            return json.loads(private_key.strip())
        except json.JSONDecodeError as exc:
            raise ValueError("Private key must be valid JSON.") from exc

    @staticmethod
    def _determine_alg_from_jwk(jwk: PrivateJwk) -> str:
        if "alg" in jwk:
            return jwk["alg"]

        kty = jwk.get("kty")
        if kty == "RSA":
            return "RS256"
        if kty == "EC":
            crv = jwk.get("crv", "P-256")
            return EC_CURVE_ALG_MAP.get(crv, "ES256")

        return "RS256"

    def _get_token(self) -> AuthBase:
        try:
            from requests_oauth2client.exceptions import OAuth2Error

            return self._oauth_client.client_credentials(
                scope=" ".join(self.scopes), dpop_key=self._dpop_key
            )
        except ImportError as e:
            raise ConnectionException(
                "The 'requests-oauth2client' library is required for Okta connector. "
                "Please install it with: pip install requests-oauth2client"
            ) from e
        except OAuth2Error as e:
            raise ConnectionException(
                f"OAuth2 token acquisition failed: {str(e)}"
            ) from e

    def list_applications(
        self, limit: int = DEFAULT_API_LIMIT, after: Optional[str] = None
    ) -> Tuple[List[OktaApplication], Optional[str]]:
        """
        List Okta applications with cursor-based pagination.

        Args:
            limit: Maximum number of applications to return
            after: Cursor for next page (from previous response)

        Returns:
            Tuple of (apps_list, next_cursor). next_cursor is None if no more pages.
        """
        token = self._get_token()
        params: Dict[str, Union[int, str]] = {"limit": limit}
        if after:
            params["after"] = after

        try:
            response = requests.get(
                f"{self.org_url}/api/v1/apps",
                params=params,
                auth=token,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionException(f"Okta API request failed: {str(e)}") from e

        next_cursor = self._extract_next_cursor(response.headers.get("Link"))
        return response.json(), next_cursor

    def list_all_applications(
        self, page_size: int = DEFAULT_API_LIMIT, max_pages: int = DEFAULT_MAX_PAGES
    ) -> List[OktaApplication]:
        """
        Fetch all Okta applications with automatic pagination.

        Args:
            page_size: Number of applications per page
            max_pages: Maximum number of pages to fetch (safety limit)

        Returns:
            List of all applications
        """
        all_apps: List[OktaApplication] = []
        cursor: Optional[str] = None
        seen_cursors: set = set()

        for _ in range(max_pages):
            apps, next_cursor = self.list_applications(limit=page_size, after=cursor)
            all_apps.extend(apps)

            if not next_cursor:
                break
            if next_cursor in seen_cursors:
                break

            seen_cursors.add(next_cursor)
            cursor = next_cursor

        return all_apps

    @staticmethod
    def _extract_bracketed_url(text: str) -> Optional[str]:
        """Extract URL from angle brackets in RFC 8288 Link header format.

        Args:
            text: A link entry like '<https://example.com>; rel="next"'

        Returns:
            The URL string, or None if no bracketed URL found
        """
        start = text.find("<")
        end = text.find(">", start + 1) if start != -1 else -1
        if start != -1 and end != -1:
            return text[start + 1 : end]
        return None

    @staticmethod
    def _extract_next_cursor(link_header: Optional[str]) -> Optional[str]:
        """Extract 'after' cursor from Okta Link header.

        Args:
            link_header: The Link header from Okta API response

        Returns:
            The 'after' cursor value, or None if no next page
        """
        if not link_header:
            return None
        for link in link_header.split(","):
            if 'rel="next"' in link:
                url = OktaHttpClient._extract_bracketed_url(link)
                if url:
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query)
                    after_values = query_params.get("after", [])
                    if after_values:
                        return after_values[0]
        return None
