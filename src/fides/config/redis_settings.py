from typing import Optional
from urllib.parse import quote, quote_plus, urlencode

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__REDIS__"


class RedisSettings(FidesSettings):
    """Configuration settings for Redis."""

    charset: str = Field(
        default="utf8",
        description="Character set to use for Redis, defaults to 'utf8'. Not recommended to change.",
    )
    db_index: int = Field(
        default=0,
        description="The application will use this index in the Redis cache to cache data.",
    )
    decode_responses: bool = Field(
        default=True,
        description="Whether or not to automatically decode the values fetched from Redis. Decodes using the `charset` configuration value.",
    )
    default_ttl_seconds: int = Field(
        default=604800,
        description="The number of seconds for which data will live in Redis before automatically expiring.",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the application's Redis cache should be enabled. Only set to false for certain narrow uses of the application.",
    )
    host: str = Field(
        default="redis",
        description="The network address for the application Redis cache.",
    )
    identity_verification_code_ttl_seconds: int = Field(
        default=600,
        description="Sets TTL for cached identity verification code as part of subject requests.",
    )
    password: str = Field(
        default="testpassword",
        description="The password with which to login to the Redis cache.",
    )
    port: int = Field(
        default=6379,
        description="The port at which the application cache will be accessible.",
    )
    ssl: bool = Field(
        default=False,
        description="Whether the application's connections to the cache should be encrypted using TLS.",
    )
    ssl_cert_reqs: Optional[str] = Field(
        default="required",
        description="If using TLS encryption, set this to 'required' if you wish to enforce the Redis cache to provide a certificate. Note that not all cache providers support this without setting ssl_ca_certs (e.g. AWS Elasticache).",
    )
    ssl_ca_certs: str = Field(
        default="",
        description="If using TLS encryption rooted with a custom Certificate Authority, set this to the path of the CA certificate.",
    )
    user: str = Field(
        default="", description="The user with which to login to the Redis cache."
    )

    # This relies on other values to get built so must be last
    connection_url: Optional[str] = Field(
        default=None,
        description="A full connection URL to the Redis cache. If not specified, this URL is automatically assembled from the host, port, password and db_index specified above.",
        exclude=True,
    )

    @field_validator("connection_url", mode="before")
    @classmethod
    def assemble_connection_url(
        cls,
        v: Optional[str],
        info: ValidationInfo,
    ) -> str:
        """Join Redis connection credentials into a connection string"""
        if isinstance(v, str):
            # If the whole URL is provided via the config, preference that
            return v

        connection_protocol = "redis"
        params_str = ""
        use_tls = info.data.get("ssl", False)

        # These vars are intentionally fetched with `or ""` as the default to account
        # for the edge case where `None` is explicitly set in `values` by Pydantic because
        # it is not overridden by the config file or an env var
        user = info.data.get("user") or ""
        password = info.data.get("password") or ""
        db_index = info.data.get("db_index") or ""
        if use_tls:
            # If using TLS update the connection URL format
            connection_protocol = "rediss"
            cert_reqs = info.data.get("ssl_cert_reqs", "none")
            params = {"ssl_cert_reqs": quote_plus(cert_reqs)}
            if ssl_ca_certs := info.data.get("ssl_ca_certs", ""):
                params["ssl_ca_certs"] = quote(ssl_ca_certs, safe="/")
            params_str = "?" + urlencode(params, quote_via=quote, safe="/")

        # Configure a basic auth prefix if either user or password is provided, e.g.
        # redis://<user>:<password>@<host>
        auth_prefix = ""
        if password or user:
            auth_prefix = f"{quote_plus(user)}:{quote_plus(password)}@"

        connection_url = f"{connection_protocol}://{auth_prefix}{info.data.get('host', '')}:{info.data.get('port', '')}/{db_index}{params_str}"
        return connection_url

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
