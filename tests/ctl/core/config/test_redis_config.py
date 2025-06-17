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
        """Test that read_only_user falls back to user when not set."""
        redis_settings = RedisSettings(user="writer_user")
        assert redis_settings.read_only_user == "writer_user"

    def test_read_only_user_explicit_value(self) -> None:
        """Test that read_only_user uses explicit value when provided."""
        redis_settings = RedisSettings(
            user="writer_user", read_only_user="readonly_user"
        )
        assert redis_settings.read_only_user == "readonly_user"

    def test_read_only_user_empty_string_explicit(self) -> None:
        """Test that read_only_user respects explicit empty string."""
        redis_settings = RedisSettings(user="writer_user", read_only_user="")
        assert redis_settings.read_only_user == ""

    def test_read_only_port_fallback(self) -> None:
        """Test that read_only_port falls back to port when not set."""
        redis_settings = RedisSettings(port=9999)
        assert redis_settings.read_only_port == 9999

    def test_read_only_port_fallback_to_writer_default(self) -> None:
        """Test that read_only_port uses port default when neither are set."""
        redis_settings = RedisSettings()
        assert redis_settings.read_only_port == 6379  # default port

    def test_read_only_port_explicit_value(self) -> None:
        """Test that read_only_port uses explicit value when provided."""
        redis_settings = RedisSettings(port=6379, read_only_port=1234)
        assert redis_settings.read_only_port == 1234

    def test_read_only_password_fallback(self) -> None:
        """Test that read_only_password falls back to password when not set."""
        redis_settings = RedisSettings(password="writer_pass")
        assert redis_settings.read_only_password == "writer_pass"

    def test_read_only_password_explicit_value(self) -> None:
        """Test that read_only_password uses explicit value when provided."""
        redis_settings = RedisSettings(
            password="writer_pass", read_only_password="readonly_pass"
        )
        assert redis_settings.read_only_password == "readonly_pass"

    def test_read_only_db_index_fallback(self) -> None:
        """Test that read_only_db_index falls back to db_index when not set."""
        redis_settings = RedisSettings(db_index=5)
        assert redis_settings.read_only_db_index == 5

    def test_read_only_db_index_explicit_value(self) -> None:
        """Test that read_only_db_index uses explicit value when provided."""
        redis_settings = RedisSettings(db_index=0, read_only_db_index=7)
        assert redis_settings.read_only_db_index == 7

    def test_read_only_ssl_fallback(self) -> None:
        """Test that read_only_ssl falls back to ssl when not set."""
        redis_settings = RedisSettings(ssl=True)
        assert redis_settings.read_only_ssl is True

    def test_read_only_ssl_explicit_value(self) -> None:
        """Test that read_only_ssl uses explicit value when provided."""
        redis_settings = RedisSettings(ssl=False, read_only_ssl=True)
        assert redis_settings.read_only_ssl is True

    def test_read_only_ssl_cert_reqs_fallback(self) -> None:
        """Test that read_only_ssl_cert_reqs falls back to ssl_cert_reqs when not set."""
        redis_settings = RedisSettings(ssl_cert_reqs="none")
        assert redis_settings.read_only_ssl_cert_reqs == "none"

    def test_read_only_ssl_cert_reqs_explicit_value(self) -> None:
        """Test that read_only_ssl_cert_reqs uses explicit value when provided."""
        redis_settings = RedisSettings(
            ssl_cert_reqs="required", read_only_ssl_cert_reqs="optional"
        )
        assert redis_settings.read_only_ssl_cert_reqs == "optional"

    def test_read_only_ssl_ca_certs_fallback(self) -> None:
        """Test that read_only_ssl_ca_certs falls back to ssl_ca_certs when not set."""
        redis_settings = RedisSettings(ssl_ca_certs="/path/to/cert")
        assert redis_settings.read_only_ssl_ca_certs == "/path/to/cert"

    def test_read_only_ssl_ca_certs_explicit_value(self) -> None:
        """Test that read_only_ssl_ca_certs uses explicit value when provided."""
        redis_settings = RedisSettings(
            ssl_ca_certs="/path/to/writer", read_only_ssl_ca_certs="/path/to/readonly"
        )
        assert redis_settings.read_only_ssl_ca_certs == "/path/to/readonly"

    def test_connection_url_uses_fallback_values(self) -> None:
        """Test that read_only_connection_url uses fallback values for unset read-only fields."""
        redis_settings = RedisSettings(
            user="writer_user",
            password="writer_pass",
            port=9999,
            db_index=3,
            read_only_enabled=True,
            read_only_host="readonly-host",
            # read_only_user, read_only_password, read_only_port, read_only_db_index not set - should fallback
        )

        expected_url = "redis://writer_user:writer_pass@readonly-host:9999/3"
        assert redis_settings.read_only_connection_url == expected_url

    def test_fields_are_type_safe(self) -> None:
        """Test that the fallback fields maintain proper types after resolution."""
        redis_settings = RedisSettings(
            port=6379,
            user="test_user",
            password="test_pass",
            db_index=1,
            ssl=True,
            ssl_cert_reqs="required",
            ssl_ca_certs="/path/to/cert",
        )

        # These should all be resolved to the writer values with correct types
        assert isinstance(redis_settings.read_only_port, int)
        assert isinstance(redis_settings.read_only_user, str)
        assert isinstance(redis_settings.read_only_password, str)
        assert isinstance(redis_settings.read_only_db_index, int)
        assert isinstance(redis_settings.read_only_ssl, bool)
        assert isinstance(redis_settings.read_only_ssl_cert_reqs, (str, type(None)))
        assert isinstance(redis_settings.read_only_ssl_ca_certs, str)
