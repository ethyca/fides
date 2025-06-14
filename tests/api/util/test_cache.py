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
                port=enable_read_only_cache_settings.redis.read_only_port,
                db=1,  # test_db_index in test mode
                username=enable_read_only_cache_settings.redis.read_only_user,
                password=enable_read_only_cache_settings.redis.read_only_password,
                ssl=enable_read_only_cache_settings.redis.read_only_ssl,
                ssl_ca_certs=enable_read_only_cache_settings.redis.read_only_ssl_ca_certs,
                ssl_cert_reqs=enable_read_only_cache_settings.redis.read_only_ssl_cert_reqs,
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
