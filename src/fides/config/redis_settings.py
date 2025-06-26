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
    test_db_index: int = Field(
        default=1,
        description="The application will use this index in the Redis cache to cache data for testing.",
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

    # Read-only Redis settings
    read_only_enabled: bool = Field(
        default=False,
        description="Whether a read-only Redis cache is enabled.",
    )
    read_only_host: str = Field(
        default="",
        description="The network address for the read-only Redis cache.",
    )
    # Read-only Redis settings with automatic fallback behavior
    # Field validators will populate these fields with the corresponding writer settings if not provided
    # The order here is important, these must be defined after the writer settings
    read_only_port: int = Field(  # type: ignore[assignment]
        default=None,
        description="The port at which the read-only Redis cache will be accessible. If not provided, the `port` setting will be used.",
    )
    read_only_user: str = Field(  # type: ignore[assignment]
        default=None,
        description="The user with which to login to the read-only Redis cache. If not provided, the `user` setting will be used.",
    )
    read_only_password: str = Field(  # type: ignore[assignment]
        default=None,
        description="The password with which to login to the read-only Redis cache. If not provided, the `password` setting will be used.",
    )
    read_only_db_index: int = Field(  # type: ignore[assignment]
        default=None,
        description="The application will use this index in the read-only Redis cache to cache data. If not provided, the `db_index` setting will be used.",
    )
    read_only_ssl: bool = Field(  # type: ignore[assignment]
        default=None,
        description="Whether the application's connections to the read-only cache should be encrypted using TLS. If not provided, the `ssl` setting will be used.",
    )
    read_only_ssl_cert_reqs: Optional[str] = Field(
        default=None,
        description="If using TLS encryption, set this to 'required' if you wish to enforce the read-only Redis cache to provide a certificate. Note that not all cache providers support this without setting ssl_ca_certs (e.g. AWS Elasticache). If not provided, the `ssl_cert_reqs` setting will be used.",
    )
    read_only_ssl_ca_certs: str = Field(  # type: ignore[assignment]
        default=None,
        description="If using TLS encryption rooted with a custom Certificate Authority, set this to the path of the CA certificate. If not provided, the `ssl_ca_certs` setting will be used.",
    )

    # Field validators for automatic fallback behavior
    @field_validator("read_only_port", mode="before")
    @classmethod
    def resolve_read_only_port(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Resolves the read-only port setting by falling back to the `port` value if no `read_only_port` is specified."""
        if v is None:
            return info.data["port"]
        return v

    @field_validator("read_only_user", mode="before")
    @classmethod
    def resolve_read_only_user(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Resolves the read-only user setting by falling back to the `user` value if no `read_only_user` is specified."""
        if v is None:
            return info.data["user"]
        return v

    @field_validator("read_only_password", mode="before")
    @classmethod
    def resolve_read_only_password(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Resolves the read-only password setting by falling back to the `password` value if no `read_only_password` is specified."""
        if v is None:
            return info.data["password"]
        return v

    @field_validator("read_only_db_index", mode="before")
    @classmethod
    def resolve_read_only_db_index(cls, v: Optional[int], info: ValidationInfo) -> int:
        """Resolves the read-only db_index setting by falling back to the `db_index` value if no `read_only_db_index` is specified."""
        if v is None:
            return info.data["db_index"]
        return v

    @field_validator("read_only_ssl", mode="before")
    @classmethod
    def resolve_read_only_ssl(cls, v: Optional[bool], info: ValidationInfo) -> bool:
        """Resolves the read-only ssl setting by falling back to the `ssl` value if no `read_only_ssl` is specified."""
        if v is None:
            return info.data["ssl"]
        return v

    @field_validator("read_only_ssl_cert_reqs", mode="before")
    @classmethod
    def resolve_read_only_ssl_cert_reqs(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Resolves the read-only ssl_cert_reqs setting by falling back to the `ssl_cert_reqs` value if no `read_only_ssl_cert_reqs` is specified."""
        if v is None:
            return info.data["ssl_cert_reqs"]
        return v

    @field_validator("read_only_ssl_ca_certs", mode="before")
    @classmethod
    def resolve_read_only_ssl_ca_certs(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        """Resolves the read-only ssl_ca_certs setting by falling back to the `ssl_ca_certs` value if no `read_only_ssl_ca_certs` is specified."""
        if v is None:
            return info.data["ssl_ca_certs"]
        return v

    # This relies on other values to get built so must be last
    connection_url: Optional[str] = Field(
        default=None,
        description="A full connection URL to the Redis cache. If not specified, this URL is automatically assembled from the host, port, password and db_index specified above.",
        exclude=True,
    )
    read_only_connection_url: Optional[str] = Field(
        default=None,
        description="A full connection URL to the read-only Redis cache. If not specified, this URL is automatically assembled from the read_only_host, read_only_port, read_only_password and read_only_db_index specified above.",
        exclude=True,
    )

    @field_validator("connection_url", "read_only_connection_url", mode="before")
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

        # Determine which set of settings to use based on field name
        is_read_only = info.field_name == "read_only_connection_url"

        # Extract settings - fallbacks already resolved by field validators for read-only fields
        user = (
            info.data["read_only_user"] if is_read_only else info.data.get("user", "")
        )
        password = (
            info.data["read_only_password"]
            if is_read_only
            else info.data.get("password", "")
        )

        db_index = (
            info.data["read_only_db_index"]
            if is_read_only
            else info.data.get("db_index", "")
        )
        use_tls = (
            info.data["read_only_ssl"] if is_read_only else info.data.get("ssl", False)
        )

        connection_protocol = "redis"
        params_str = ""

        if use_tls:
            # If using TLS update the connection URL format
            connection_protocol = "rediss"

            ssl_cert_reqs = (
                info.data.get("read_only_ssl_cert_reqs", "none")
                if is_read_only
                else info.data.get("ssl_cert_reqs", "none")
            )
            ssl_ca_certs = (
                info.data["read_only_ssl_ca_certs"]
                if is_read_only
                else info.data.get("ssl_ca_certs", "")
            )

            # Build SSL parameters
            params = {"ssl_cert_reqs": quote_plus(ssl_cert_reqs or "none")}
            if ssl_ca_certs:
                params["ssl_ca_certs"] = quote(ssl_ca_certs, safe="/")
            params_str = "?" + urlencode(params, quote_via=quote, safe="/")

        # Configure a basic auth prefix if either user or password is provided, e.g.
        # redis://<user>:<password>@<host>
        auth_prefix = ""
        if password or user:
            auth_prefix = f"{quote_plus(user)}:{quote_plus(password)}@"

        # For host, we don't have a fallback - read replica should be a different host
        host = (
            info.data.get("read_only_host", "")
            if is_read_only
            else info.data.get("host", "")
        )
        port = (
            info.data["read_only_port"] if is_read_only else info.data.get("port", "")
        )
        # Only include database index in URL if it's not the default (0)
        db_path = f"{db_index}" if db_index != 0 else ""

        connection_url = (
            f"{connection_protocol}://{auth_prefix}{host}:{port}/{db_path}{params_str}"
        )
        return connection_url

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
