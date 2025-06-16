from typing import Any, Optional
from urllib.parse import quote, quote_plus, urlencode

from pydantic import Field, ValidationInfo, computed_field, field_validator
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

    # Read-only Redis settings (storage fields)
    read_only_enabled: bool = Field(
        default=False,
        description="Whether a read-only Redis cache is enabled.",
    )
    read_only_host: str = Field(
        default="",
        description="The network address for the read-only Redis cache.",
    )
    read_only_port: Optional[int] = Field(
        default=None,
        description="The port at which the read-only Redis cache will be accessible.",
    )
    read_only_user: Optional[str] = Field(
        default=None,
        description="The user with which to login to the read-only Redis cache. If not provided, the user setting will be used.",
    )
    read_only_password: Optional[str] = Field(
        default=None,
        description="The password with which to login to the read-only Redis cache. If not provided, the password setting will be used.",
    )
    read_only_db_index: Optional[int] = Field(
        default=None,
        description="The application will use this index in the read-only Redis cache to cache data. If not provided, the db_index setting will be used.",
    )
    read_only_ssl: Optional[bool] = Field(
        default=None,
        description="Whether the application's connections to the read-only cache should be encrypted using TLS. If not provided, the ssl setting will be used.",
    )
    read_only_ssl_cert_reqs: Optional[str] = Field(
        default=None,
        description="If using TLS encryption, set this to 'required' if you wish to enforce the read-only Redis cache to provide a certificate. Note that not all cache providers support this without setting ssl_ca_certs (e.g. AWS Elasticache). If not provided, the ssl_cert_reqs setting will be used.",
    )
    read_only_ssl_ca_certs: Optional[str] = Field(
        default=None,
        description="If using TLS encryption rooted with a custom Certificate Authority, set this to the path of the CA certificate. If not provided, the ssl_ca_certs setting will be used.",
    )

    # Computed fields for read-only settings with automatic fallback behavior
    # If the read-only setting is not provided, we will fall back to the corresponding writer setting.
    @computed_field  # type: ignore[misc]
    @property
    def read_only_port_resolved(self) -> int:
        """Port for read-only Redis, falls back to writer port if not set."""
        return self.read_only_port if self.read_only_port is not None else self.port

    @computed_field  # type: ignore[misc]
    @property
    def read_only_user_resolved(self) -> str:
        """User for read-only Redis, falls back to writer user if not set."""
        return self.read_only_user if self.read_only_user is not None else self.user

    @computed_field  # type: ignore[misc]
    @property
    def read_only_password_resolved(self) -> str:
        """Password for read-only Redis, falls back to writer password if not set."""
        return (
            self.read_only_password
            if self.read_only_password is not None
            else self.password
        )

    @computed_field  # type: ignore[misc]
    @property
    def read_only_db_index_resolved(self) -> int:
        """DB index for read-only Redis, falls back to writer db_index if not set."""
        return (
            self.read_only_db_index
            if self.read_only_db_index is not None
            else self.db_index
        )

    @computed_field  # type: ignore[misc]
    @property
    def read_only_ssl_resolved(self) -> bool:
        """SSL setting for read-only Redis, falls back to writer ssl if not set."""
        return self.read_only_ssl if self.read_only_ssl is not None else self.ssl

    @computed_field  # type: ignore[misc]
    @property
    def read_only_ssl_cert_reqs_resolved(self) -> Optional[str]:
        """SSL cert requirements for read-only Redis, falls back to writer ssl_cert_reqs if not set."""
        return (
            self.read_only_ssl_cert_reqs
            if self.read_only_ssl_cert_reqs is not None
            else self.ssl_cert_reqs
        )

    @computed_field  # type: ignore[misc]
    @property
    def read_only_ssl_ca_certs_resolved(self) -> str:
        """SSL CA certs for read-only Redis, falls back to writer ssl_ca_certs if not set."""
        return (
            self.read_only_ssl_ca_certs
            if self.read_only_ssl_ca_certs is not None
            else self.ssl_ca_certs
        )

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

        # For the read-only connection settings, if a setting is not provided, we will
        # fall back to the corresponding writable setting.
        is_read_only = info.field_name == "read_only_connection_url"

        def get_setting_with_fallback(
            read_only_key: str, writer_key: str, default_value: Any = ""
        ) -> Any:
            """Helper to get setting with fallback logic for read-only connections."""
            # If we're returning the regular writer connection, just return the value from the writer key
            writer_value = info.data.get(writer_key, default_value)
            if not is_read_only:
                return writer_value

            read_only_value = info.data.get(read_only_key)
            # If we have a read-only value, return it
            if read_only_value is not None:
                return read_only_value

            # If we don't have a read-only value, return the writer value as fallback
            return writer_value

        connection_protocol = "redis"
        params_str = ""

        use_tls = get_setting_with_fallback("read_only_ssl", "ssl", False)
        user = get_setting_with_fallback("read_only_user", "user", "")
        password = get_setting_with_fallback("read_only_password", "password", "")
        db_index = get_setting_with_fallback("read_only_db_index", "db_index", "")

        if use_tls:
            # If using TLS update the connection URL format
            connection_protocol = "rediss"

            cert_reqs = get_setting_with_fallback(
                "read_only_ssl_cert_reqs", "ssl_cert_reqs", "none"
            )
            params = {"ssl_cert_reqs": quote_plus(cert_reqs)}

            ssl_ca_certs = get_setting_with_fallback(
                "read_only_ssl_ca_certs", "ssl_ca_certs", ""
            )
            if ssl_ca_certs:
                params["ssl_ca_certs"] = quote(ssl_ca_certs, safe="/")
            params_str = "?" + urlencode(params, quote_via=quote, safe="/")

        # Configure a basic auth prefix if either user or password is provided, e.g.
        # redis://<user>:<password>@<host>
        auth_prefix = ""
        if password or user:
            auth_prefix = f"{quote_plus(user)}:{quote_plus(password)}@"

        # For host only, we don't want to fall back to the writer host, since the
        # read replica should be a different host.
        host = (
            info.data.get("read_only_host", "")
            if is_read_only
            else info.data.get("host", "")
        )

        port = get_setting_with_fallback("read_only_port", "port", "")

        # Only include database index in URL if it's not the default (0)
        db_path = f"{db_index}" if db_index != 0 else ""

        connection_url = (
            f"{connection_protocol}://{auth_prefix}{host}:{port}/{db_path}{params_str}"
        )
        return connection_url

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
