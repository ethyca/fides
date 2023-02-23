from typing import Dict, Optional
from urllib.parse import quote_plus

from pydantic import validator

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__REDIS__"


class RedisSettings(FidesSettings):
    """Configuration settings for Redis."""

    host: str = "redis"
    port: int = 6379
    user: Optional[str] = None
    password: Optional[str] = None
    charset: str = "utf8"
    decode_responses: bool = True
    default_ttl_seconds: int = 604800
    identity_verification_code_ttl_seconds: int = 600
    db_index: Optional[int]
    enabled: bool = False
    ssl: bool = False
    ssl_cert_reqs: Optional[str] = "required"
    connection_url: Optional[str] = None

    @validator("connection_url", pre=True)
    @classmethod
    def assemble_connection_url(
        cls,
        v: Optional[str],
        values: Dict[str, str],
    ) -> str:
        """Join Redis connection credentials into a connection string"""
        if isinstance(v, str):
            # If the whole URL is provided via the config, preference that
            return v

        connection_protocol = "redis"
        params = ""
        use_tls = values.get("ssl", False)

        # These vars are intentionally fetched with `or ""` as the default to account
        # for the edge case where `None` is explicitly set in `values` by Pydantic because
        # it is not overridden by the config file or an env var
        user = values.get("user") or ""
        password = values.get("password") or ""
        db_index = values.get("db_index") or ""
        if use_tls:
            # If using TLS update the connection URL format
            connection_protocol = "rediss"
            cert_reqs = values.get("ssl_cert_reqs", "none")
            params = f"?ssl_cert_reqs={quote_plus(cert_reqs)}"

        # Configure a basic auth prefix if either user or password is provided, e.g.
        # redis://<user>:<password>@<host>
        auth_prefix = ""
        if password or user:
            auth_prefix = f"{quote_plus(user)}:{quote_plus(password)}@"

        return f"{connection_protocol}://{auth_prefix}{values.get('host', '')}:{values.get('port', '')}/{db_index}{params}"

    class Config:
        env_prefix = ENV_PREFIX
