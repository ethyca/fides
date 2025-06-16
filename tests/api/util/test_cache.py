from unittest.mock import MagicMock, patch

import pytest

from fides.api import common_exceptions
from fides.api.util.cache import get_read_only_cache


class TestGetReadOnlyCache:
    @pytest.fixture(scope="function")
    def disable_redis_cache(self, config):
        """Fixture to disable Redis cache for testing"""
        assert config.test_mode
        original_value = config.redis.enabled
        config.redis.enabled = False
        yield config
        config.redis.enabled = original_value

    @pytest.fixture(scope="function")
    def disable_read_only_cache(self, config):
        """Fixture to disable read-only cache for testing"""
        assert config.test_mode
        original_value = config.redis.read_only_enabled
        config.redis.read_only_enabled = False
        yield config
        config.redis.read_only_enabled = original_value

    @pytest.fixture(scope="function")
    def enable_read_only_cache_settings(self, config):
        """Fixture to enable read-only cache for testing"""
        assert config.test_mode
        original_value = config.redis.read_only_enabled
        original_value_host = config.redis.read_only_host
        original_value_port = config.redis.read_only_port
        original_value_user = config.redis.read_only_user
        original_value_password = config.redis.read_only_password
        config.redis.read_only_enabled = True
        config.redis.read_only_host = "test-read-only-host"
        config.redis.read_only_port = 12345
        config.redis.read_only_user = "test-read-only-user"
        config.redis.read_only_password = "test-read-only-password"
        yield config
        config.redis.read_only_enabled = original_value
        config.redis.read_only_host = original_value_host
        config.redis.read_only_port = original_value_port
        config.redis.read_only_user = original_value_user
        config.redis.read_only_password = original_value_password

    @pytest.fixture(scope="function")
    def enable_read_only_cache_with_fallbacks(self, config):
        """Fixture to enable read-only cache but leave some settings as None to test fallbacks"""
        assert config.test_mode
        original_values = {
            "read_only_enabled": config.redis.read_only_enabled,
            "read_only_host": config.redis.read_only_host,
            "read_only_port": config.redis.read_only_port,
            "read_only_user": config.redis.read_only_user,
            "read_only_password": config.redis.read_only_password,
            "read_only_db_index": config.redis.read_only_db_index,
            "read_only_ssl": config.redis.read_only_ssl,
            "read_only_ssl_cert_reqs": config.redis.read_only_ssl_cert_reqs,
            "read_only_ssl_ca_certs": config.redis.read_only_ssl_ca_certs,
            # Also store writer values we'll modify
            "user": config.redis.user,
            "password": config.redis.password,
        }

        # Set specific writer values that we can verify are used as fallbacks
        config.redis.user = "test-writer-user"
        config.redis.password = "test-writer-password"

        # Enable read-only but set specific read-only settings to None to test fallbacks
        config.redis.read_only_enabled = True
        config.redis.read_only_host = (
            "test-read-only-host"  # This one we set explicitly
        )
        config.redis.read_only_port = None  # Should fallback to writer port
        config.redis.read_only_user = (
            None  # Should fallback to writer user (test-writer-user)
        )
        config.redis.read_only_password = (
            None  # Should fallback to writer password (test-writer-password)
        )
        config.redis.read_only_db_index = None  # Should fallback to writer db_index
        config.redis.read_only_ssl = None  # Should fallback to writer ssl
        config.redis.read_only_ssl_cert_reqs = (
            None  # Should fallback to writer ssl_cert_reqs
        )
        config.redis.read_only_ssl_ca_certs = (
            None  # Should fallback to writer ssl_ca_certs
        )

        yield config

        # Restore original values
        for key, value in original_values.items():
            setattr(config.redis, key, value)

    @pytest.fixture(scope="function", autouse=True)
    def clear_read_only_connection(self):
        """Auto-use fixture to clear the global read-only connection before and after each test"""
        import fides.api.util.cache as cache_module

        # Clear before test
        cache_module._read_only_connection = None
        yield
        # Clear after test
        cache_module._read_only_connection = None

    @pytest.mark.usefixtures("disable_redis_cache")
    def test_read_only_cache_is_not_enabled(self):
        """Test that RedisNotConfigured is raised when Redis is disabled"""
        with pytest.raises(common_exceptions.RedisNotConfigured):
            get_read_only_cache()

    @pytest.mark.usefixtures("disable_read_only_cache")
    def test_read_only_disabled_returns_regular_cache(self):
        """Test that when read-only is disabled, get_read_only_cache returns the regular cache"""
        # Mock the get_cache function
        with patch("fides.api.util.cache.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_get_cache.return_value = mock_cache

            result = get_read_only_cache()

            # Should call get_cache() and return its result
            mock_get_cache.assert_called_once()
            assert result == mock_cache

    def test_read_only_enabled_creates_new_connection(
        self, enable_read_only_cache_settings
    ):
        """Test that when read-only is enabled, a new read-only Redis connection is created"""
        # Mock FidesopsRedis to avoid actual Redis connection
        with patch("fides.api.util.cache.FidesopsRedis") as MockRedis:
            mock_redis_instance = MagicMock()
            MockRedis.return_value = mock_redis_instance

            # Mock ping to return True (successful connection)
            mock_redis_instance.ping.return_value = True

            result = get_read_only_cache()

            # Should create a new FidesopsRedis instance with read-only config
            MockRedis.assert_called_once_with(
                charset=enable_read_only_cache_settings.redis.charset,
                decode_responses=enable_read_only_cache_settings.redis.decode_responses,
                host=enable_read_only_cache_settings.redis.read_only_host,
                port=enable_read_only_cache_settings.redis.read_only_port_resolved,
                db=1,  # test_db_index in test mode
                username=enable_read_only_cache_settings.redis.read_only_user_resolved,
                password=enable_read_only_cache_settings.redis.read_only_password_resolved,
                ssl=enable_read_only_cache_settings.redis.read_only_ssl_resolved,
                ssl_ca_certs=enable_read_only_cache_settings.redis.read_only_ssl_ca_certs_resolved,
                ssl_cert_reqs=enable_read_only_cache_settings.redis.read_only_ssl_cert_reqs_resolved,
            )

            # Should ping to test connection
            mock_redis_instance.ping.assert_called_once()
            assert result == mock_redis_instance

    @pytest.mark.usefixtures("enable_read_only_cache_settings")
    def test_read_only_connection_fails_fallback_to_regular_cache(self):
        """Test that when read-only connection fails, it falls back to regular cache"""
        # Mock FidesopsRedis to simulate connection failure
        with (
            patch("fides.api.util.cache.FidesopsRedis") as MockRedis,
            patch("fides.api.util.cache.get_cache") as mock_get_cache,
        ):

            mock_redis_instance = MagicMock()
            MockRedis.return_value = mock_redis_instance

            # Mock ping to raise ConnectionError (failed connection)
            from redis.exceptions import ConnectionError as ConnectionErrorFromRedis

            mock_redis_instance.ping.side_effect = ConnectionErrorFromRedis(
                "Connection failed"
            )

            mock_regular_cache = MagicMock()
            mock_get_cache.return_value = mock_regular_cache

            result = get_read_only_cache()

            # Should attempt to create read-only connection
            MockRedis.assert_called_once()
            mock_redis_instance.ping.assert_called_once()

            # Should fallback to regular cache
            mock_get_cache.assert_called_once()
            assert result == mock_regular_cache

    @pytest.mark.usefixtures("enable_read_only_cache_settings")
    def test_read_only_connection_any_exception_fallback_to_regular_cache(self):
        """Test that when any exception occurs during read-only connection, it falls back to regular cache"""
        # Mock FidesopsRedis to simulate any exception during connection
        with (
            patch("fides.api.util.cache.FidesopsRedis") as MockRedis,
            patch("fides.api.util.cache.get_cache") as mock_get_cache,
        ):

            mock_redis_instance = MagicMock()
            MockRedis.return_value = mock_redis_instance

            # Mock ping to raise a generic Exception (not just Redis-specific errors)
            mock_redis_instance.ping.side_effect = Exception(
                "Unexpected error during connection"
            )

            mock_regular_cache = MagicMock()
            mock_get_cache.return_value = mock_regular_cache

            result = get_read_only_cache()

            # Should attempt to create read-only connection
            MockRedis.assert_called_once()
            mock_redis_instance.ping.assert_called_once()

            # Should fallback to regular cache
            mock_get_cache.assert_called_once()
            assert result == mock_regular_cache

    def test_read_only_cache_uses_fallback_settings(
        self, enable_read_only_cache_with_fallbacks
    ):
        """Test that read-only cache uses writer settings as fallbacks when read-only settings are None"""
        # Mock FidesopsRedis to avoid actual Redis connection
        with patch("fides.api.util.cache.FidesopsRedis") as MockRedis:
            mock_redis_instance = MagicMock()
            MockRedis.return_value = mock_redis_instance

            # Mock ping to return True (successful connection)
            mock_redis_instance.ping.return_value = True

            result = get_read_only_cache()

            # Should create a new FidesopsRedis instance with fallback values
            MockRedis.assert_called_once_with(
                charset=enable_read_only_cache_with_fallbacks.redis.charset,
                decode_responses=enable_read_only_cache_with_fallbacks.redis.decode_responses,
                host=enable_read_only_cache_with_fallbacks.redis.read_only_host,  # This was set explicitly
                port=enable_read_only_cache_with_fallbacks.redis.read_only_port_resolved,  # Fallback to writer port
                db=1,  # test_db_index in test mode
                username=enable_read_only_cache_with_fallbacks.redis.read_only_user_resolved,  # Fallback to writer user we set in fixture
                password=enable_read_only_cache_with_fallbacks.redis.read_only_password_resolved,  # Fallback to writer password we set in fixture
                ssl=enable_read_only_cache_with_fallbacks.redis.read_only_ssl_resolved,  # Fallback to writer ssl
                ssl_ca_certs=enable_read_only_cache_with_fallbacks.redis.read_only_ssl_ca_certs_resolved,  # Fallback to writer ssl_ca_certs
                ssl_cert_reqs=enable_read_only_cache_with_fallbacks.redis.read_only_ssl_cert_reqs_resolved,  # Fallback to writer ssl_cert_reqs
            )

            # Should ping to test connection
            mock_redis_instance.ping.assert_called_once()
            assert result == mock_redis_instance
