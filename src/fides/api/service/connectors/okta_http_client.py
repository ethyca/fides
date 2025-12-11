import json
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import requests
from requests.adapters import HTTPAdapter
from typing_extensions import TypedDict
from urllib3.util.retry import Retry

from fides.api.common_exceptions import ConnectionException
from fides.api.service.connectors.limiter.rate_limiter import (
    RateLimiter,
    RateLimiterPeriod,
    RateLimiterRequest,
)

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

# Rate limiting: Okta's default is 600 requests/minute for most endpoints
# https://developer.okta.com/docs/reference/rl-global-mgmt/
DEFAULT_RATE_LIMIT_PER_MINUTE = 500  # Conservative default below Okta's limit

EC_CURVE_ALG_MAP = {
    "P-256": "ES256",
    "P-384": "ES384",
    "P-521": "ES512",
}


class OktaHttpClient:
    """
    HTTP client for Okta API with OAuth2 private_key_jwt + DPoP.

    Uses custom implementation instead of Okta SDK because the SDK lacks DPoP support.

    Features:
    - Automatic token management via OAuth2ClientCredentialsAuth (10-minute refresh buffer)
    - Rate limiting via Redis (gracefully degrades if Redis unavailable)
    - Retry with exponential backoff for transient failures (429, 5xx) via urllib3
    """

    def __init__(
        self,
        org_url: str,
        client_id: str,
        private_key: Union[str, PrivateJwk],
        scopes: Optional[List[str]] = None,
        *,
        rate_limit_per_minute: Optional[int] = DEFAULT_RATE_LIMIT_PER_MINUTE,
        session: Optional[requests.Session] = None,  # For test injection
    ):
        self.org_url = org_url.rstrip("/")
        self.scopes = tuple(scopes) if scopes is not None else DEFAULT_OKTA_SCOPES

        # Rate limiting configuration
        self._rate_limit_per_minute = rate_limit_per_minute

        # Allow test injection of a pre-configured session
        if session is not None:
            self._session = session
            return

        try:
            from requests_oauth2client import (
                DPoPKey,
                OAuth2Client,
                OAuth2ClientCredentialsAuth,
                PrivateKeyJwt,
            )

            private_jwk = self._parse_jwk(private_key)
            alg = self._determine_alg_from_jwk(private_jwk)

            # DPoP (RFC 9449) requires a separate key from client authentication.
            # ES256 is used regardless of the client auth key type because:
            # 1. It's explicitly recommended by RFC 9449 for DPoP proofs
            # 2. It provides strong security with compact signatures
            # 3. Okta supports ES256 for DPoP across all configurations
            dpop_key = DPoPKey.generate(alg="ES256")

            oauth_client = OAuth2Client(
                token_endpoint=f"{self.org_url}/oauth2/v1/token",
                auth=PrivateKeyJwt(client_id, private_jwk, alg=alg),
                dpop_bound_access_tokens=True,
            )

            # Create session with automatic token management
            self._session = requests.Session()
            self._session.auth = OAuth2ClientCredentialsAuth(
                client=oauth_client,
                scope=" ".join(self.scopes),
                dpop_key=dpop_key,
                leeway=600,  # 10 min buffer before expiry (matching TOKEN_EXPIRY_BUFFER_MINUTES)
            )

            # Configure retry strategy via urllib3
            retry_strategy = Retry(
                total=3,  # 3 retries
                backoff_factor=1.0,  # Exponential backoff
                status_forcelist=[429, 502, 503, 504],  # Retryable status codes
                respect_retry_after_header=True,  # Honor Retry-After header
                raise_on_status=False,  # Let us handle errors
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)

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

        Args:
            private_key: JWK as either a JSON string or dict

        Returns:
            Parsed JWK dictionary

        Raises:
            ValueError: If key is not valid JSON or missing required 'd' parameter
        """
        if isinstance(private_key, dict):
            if "d" not in private_key:
                raise ValueError("Private key required (missing 'd' parameter)")
            return private_key

        try:
            parsed = json.loads(private_key.strip())
        except json.JSONDecodeError as exc:
            raise ValueError("Private key must be valid JSON.") from exc

        if "d" not in parsed:
            raise ValueError("Private key required (missing 'd' parameter)")
        return parsed

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

    def _build_rate_limit_requests(self) -> List[RateLimiterRequest]:
        """
        Build rate limit request objects for Okta API calls.

        Returns empty list if rate limiting is disabled (rate_limit_per_minute is None).
        """
        if self._rate_limit_per_minute is None:
            return []

        return [
            RateLimiterRequest(
                key=f"okta:{self.org_url}",
                rate_limit=self._rate_limit_per_minute,
                period=RateLimiterPeriod.MINUTE,
            )
        ]

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting before making a request."""
        rate_limit_requests = self._build_rate_limit_requests()
        if rate_limit_requests:
            RateLimiter().limit(rate_limit_requests)

    def list_applications(
        self, limit: int = DEFAULT_API_LIMIT, after: Optional[str] = None
    ) -> Tuple[List[OktaApplication], Optional[str]]:
        """
        List Okta applications with cursor-based pagination.

        Includes:
        - Rate limiting (via Redis if available)
        - Retry with exponential backoff for transient failures (via urllib3)
        - Automatic token management (via OAuth2ClientCredentialsAuth)

        Args:
            limit: Maximum number of applications to return
            after: Cursor for next page (from previous response)

        Returns:
            Tuple of (apps_list, next_cursor). next_cursor is None if no more pages.

        Raises:
            ConnectionException: If request fails after all retries
        """
        self._apply_rate_limit()

        params: Dict[str, Union[int, str]] = {"limit": limit}
        if after:
            params["after"] = after

        try:
            response = self._session.get(
                f"{self.org_url}/api/v1/apps",
                params=params,
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
        seen_cursors: set[str] = set()

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
