import pytest

from fides.config.redis_settings import RedisSettings


class TestBuildingRedisURLs:
    def test_generic(self) -> None:
        redis_settings = RedisSettings()
        assert redis_settings.connection_url == "redis://:testpassword@redis:6379/"

    def test_configured(self) -> None:
        redis_settings = RedisSettings(
            db_index=1, host="myredis", port="6380", password="supersecret"
        )
        assert redis_settings.connection_url == "redis://:supersecret@myredis:6380/1"

    def test_tls(self) -> None:
        redis_settings = RedisSettings(ssl=True, ssl_cert_reqs="none")
        assert (
            redis_settings.connection_url
            == "rediss://:testpassword@redis:6379/?ssl_cert_reqs=none"
        )

    def test_tls_custom_ca(self) -> None:
        redis_settings = RedisSettings(ssl=True, ssl_ca_certs="/path/to/my/cert.crt")
        assert (
            redis_settings.connection_url
            == "rediss://:testpassword@redis:6379/?ssl_cert_reqs=required&ssl_ca_certs=/path/to/my/cert.crt"
        )

    def test_read_only_generic(self) -> None:
        redis_settings = RedisSettings(
            read_only_enabled=True,
            read_only_host="readonly-redis",
            read_only_password="readonlypassword",
        )
        assert (
            redis_settings.read_only_connection_url
            == "redis://:readonlypassword@readonly-redis:6379/"
        )

    def test_read_only_configured(self) -> None:
        redis_settings = RedisSettings(
            read_only_enabled=True,
            read_only_db_index=1,
            read_only_host="myreadonly",
            read_only_port=6380,
            read_only_password="supersecretreadonly",
        )
        assert (
            redis_settings.read_only_connection_url
            == "redis://:supersecretreadonly@myreadonly:6380/1"
        )

    def test_read_only_tls(self) -> None:
        redis_settings = RedisSettings(
            read_only_enabled=True,
            read_only_host="readonly-redis",
            read_only_password="readonlypassword",
            read_only_ssl=True,
            read_only_ssl_cert_reqs="none",
        )
        assert (
            redis_settings.read_only_connection_url
            == "rediss://:readonlypassword@readonly-redis:6379/?ssl_cert_reqs=none"
        )

    def test_read_only_tls_custom_ca(self) -> None:
        redis_settings = RedisSettings(
            read_only_enabled=True,
            read_only_host="readonly-redis",
            read_only_password="readonlypassword",
            read_only_ssl=True,
            read_only_ssl_ca_certs="/path/to/readonly/cert.crt",
        )
        assert (
            redis_settings.read_only_connection_url
            == "rediss://:readonlypassword@readonly-redis:6379/?ssl_cert_reqs=required&ssl_ca_certs=/path/to/readonly/cert.crt"
        )


class TestRedisReadonlyFields:
    """Test the automatic fallback behavior for read-only Redis settings."""

    def test_read_only_user_fallback(self) -> None:
        """Test that read_only_user_resolved falls back to user when not set."""
        redis_settings = RedisSettings(user="writer_user")
        assert redis_settings.read_only_user_resolved == "writer_user"

    def test_read_only_user_explicit_value(self) -> None:
        """Test that read_only_user_resolved uses explicit value when provided."""
        redis_settings = RedisSettings(
            user="writer_user", read_only_user="readonly_user"
        )
        assert redis_settings.read_only_user_resolved == "readonly_user"

    def test_read_only_user_explicit_empty_string(self) -> None:
        """Test that read_only_user_resolved respects explicit empty string (no fallback)."""
        redis_settings = RedisSettings(user="writer_user", read_only_user="")
        assert redis_settings.read_only_user_resolved == ""

    def test_read_only_password_fallback(self) -> None:
        """Test that read_only_password_resolved falls back to password when not set."""
        redis_settings = RedisSettings(password="writer_password")
        assert redis_settings.read_only_password_resolved == "writer_password"

    def test_read_only_password_explicit_value(self) -> None:
        """Test that read_only_password_resolved uses explicit value when provided."""
        redis_settings = RedisSettings(
            password="writer_password", read_only_password="readonly_password"
        )
        assert redis_settings.read_only_password_resolved == "readonly_password"

    def test_read_only_port_fallback(self) -> None:
        """Test that read_only_port_resolved falls back to port when not set."""
        redis_settings = RedisSettings(port=6379)
        assert redis_settings.read_only_port_resolved == 6379

    def test_read_only_port_explicit_value(self) -> None:
        """Test that read_only_port_resolved uses explicit value when provided."""
        redis_settings = RedisSettings(port=6379, read_only_port=6380)
        assert redis_settings.read_only_port_resolved == 6380

    def test_read_only_db_index_fallback(self) -> None:
        """Test that read_only_db_index_resolved falls back to db_index when not set."""
        redis_settings = RedisSettings(db_index=2)
        assert redis_settings.read_only_db_index_resolved == 2

    def test_read_only_db_index_explicit_value(self) -> None:
        """Test that read_only_db_index_resolved uses explicit value when provided."""
        redis_settings = RedisSettings(db_index=2, read_only_db_index=3)
        assert redis_settings.read_only_db_index_resolved == 3

    def test_read_only_ssl_fallback(self) -> None:
        """Test that read_only_ssl_resolved falls back to ssl when not set."""
        redis_settings = RedisSettings(ssl=True)
        assert redis_settings.read_only_ssl_resolved is True

    def test_read_only_ssl_explicit_value(self) -> None:
        """Test that read_only_ssl_resolved uses explicit value when provided."""
        redis_settings = RedisSettings(ssl=True, read_only_ssl=False)
        assert redis_settings.read_only_ssl_resolved is False

    def test_read_only_ssl_cert_reqs_fallback(self) -> None:
        """Test that read_only_ssl_cert_reqs_resolved falls back to ssl_cert_reqs when not set."""
        redis_settings = RedisSettings(ssl_cert_reqs="none")
        assert redis_settings.read_only_ssl_cert_reqs_resolved == "none"

    def test_read_only_ssl_cert_reqs_explicit_value(self) -> None:
        """Test that read_only_ssl_cert_reqs_resolved uses explicit value when provided."""
        redis_settings = RedisSettings(
            ssl_cert_reqs="none", read_only_ssl_cert_reqs="required"
        )
        assert redis_settings.read_only_ssl_cert_reqs_resolved == "required"

    def test_read_only_ssl_ca_certs_fallback(self) -> None:
        """Test that read_only_ssl_ca_certs_resolved falls back to ssl_ca_certs when not set."""
        redis_settings = RedisSettings(ssl_ca_certs="/path/to/cert.crt")
        assert redis_settings.read_only_ssl_ca_certs_resolved == "/path/to/cert.crt"

    def test_read_only_ssl_ca_certs_explicit_value(self) -> None:
        """Test that read_only_ssl_ca_certs_resolved uses explicit value when provided."""
        redis_settings = RedisSettings(
            ssl_ca_certs="/path/to/cert.crt",
            read_only_ssl_ca_certs="/path/to/readonly/cert.crt",
        )
        assert (
            redis_settings.read_only_ssl_ca_certs_resolved
            == "/path/to/readonly/cert.crt"
        )

    def test_fallback_behavior_with_connection_url(self) -> None:
        """Test that fallback behavior works correctly in connection URL generation."""
        # Test with only writer settings - read-only should fall back
        redis_settings = RedisSettings(
            user="writer_user",
            password="writer_password",
            port=6379,
            db_index=1,
            read_only_enabled=True,
            read_only_host="readonly-host",  # Only host is different
        )

        expected_url = "redis://writer_user:writer_password@readonly-host:6379/1"
        assert redis_settings.read_only_connection_url == expected_url

    def test_no_fallback_for_non_fallback_fields(self) -> None:
        """Test that fields not in the computed fields don't have fallback behavior."""
        redis_settings = RedisSettings()

        # These fields should not have fallback behavior
        assert redis_settings.read_only_enabled is False  # Default value
        assert redis_settings.read_only_host == ""  # Default value
        assert redis_settings.read_only_connection_url is not None  # Computed field

    def test_raw_fields_still_accessible(self) -> None:
        """Test that the raw optional fields are still accessible for explicit None checking."""
        redis_settings = RedisSettings(user="writer_user")

        # Raw field should be None when not set
        assert redis_settings.read_only_user is None

        # Resolved field should fallback to writer value
        assert redis_settings.read_only_user_resolved == "writer_user"
