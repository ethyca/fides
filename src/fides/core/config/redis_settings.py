from typing import Dict, Optional
from urllib.parse import quote_plus

from pydantic import validator

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__REDIS__"


class RedisSettings(FidesSettings):
    """Configuration settings for Redis."""

    host: str = "redis"
    port: int = 6379
    user: Optional[str] = ""
    password: str = "testpassword"
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

        db_index = values.get("db_index") if values.get("db_index") is not None else ""
        connection_protocol = "redis"
        params = ""
        use_tls = values.get("ssl", False)
        if use_tls:
            # If using TLS update the connection URL format
            connection_protocol = "rediss"
            cert_reqs = values.get("ssl_cert_reqs", "none")
            params = f"?ssl_cert_reqs={quote_plus(cert_reqs)}"

        return f"{connection_protocol}://{quote_plus(values.get('user', ''))}:{quote_plus(values.get('password', ''))}@{values.get('host', '')}:{values.get('port', '')}/{db_index}{params}"

    class Config:
        env_prefix = ENV_PREFIX
