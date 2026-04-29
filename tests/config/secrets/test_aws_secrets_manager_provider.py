import json
import threading
import time
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from fides.config.secrets.aws_secrets_manager_provider import (
    AWSSecretsManagerProvider,
)
from fides.config.secrets.base import SecretProviderError, SecretValue

REGION = "us-east-1"
SECRET_NAME = "test/db-creds"
SECRET_DATA = {"username": "testuser", "password": "testpass"}


@pytest.fixture()
def aws_env():
    """Set up a moto mock with a pre-created secret."""
    with mock_aws():
        client = boto3.client("secretsmanager", region_name=REGION)
        client.create_secret(
            Name=SECRET_NAME,
            SecretString=json.dumps(SECRET_DATA),
        )
        yield client


class TestBasicFetch:
    def test_get_secret_fetches_from_aws(self, aws_env):
        provider = AWSSecretsManagerProvider(region_name=REGION)
        secret = provider.get_secret(SECRET_NAME)
        assert secret["username"] == "testuser"
        assert secret["password"] == "testpass"

    def test_get_secret_returns_secret_value_type(self, aws_env):
        provider = AWSSecretsManagerProvider(region_name=REGION)
        secret = provider.get_secret(SECRET_NAME)
        assert isinstance(secret, SecretValue)

    def test_get_secret_keys(self, aws_env):
        provider = AWSSecretsManagerProvider(region_name=REGION)
        secret = provider.get_secret(SECRET_NAME)
        assert set(secret.keys()) == {"username", "password"}

    def test_unknown_secret_raises(self, aws_env):
        provider = AWSSecretsManagerProvider(region_name=REGION)
        with pytest.raises(SecretProviderError, match="no cached value available"):
            provider.get_secret("nonexistent-secret")

    def test_invalid_json_raises_without_leaking_secret(self, aws_env):
        """If the secret value is not valid JSON, the error must not
        contain the raw secret string (which could be a plain password)."""
        raw_password = "super-secret-p@ssw0rd!"
        aws_env.update_secret(
            SecretId=SECRET_NAME,
            SecretString=raw_password,
        )
        provider = AWSSecretsManagerProvider(region_name=REGION)
        with pytest.raises(SecretProviderError) as exc_info:
            provider.get_secret(SECRET_NAME)

        # Walk the full exception chain and verify the password
        # doesn't appear anywhere
        exc = exc_info.value
        while exc is not None:
            assert raw_password not in str(exc)
            # Also check JSONDecodeError's .doc attribute if present
            if hasattr(exc, "doc"):
                raise AssertionError("JSONDecodeError with .doc leaked into chain")
            exc = exc.__cause__


class TestCaching:
    def test_second_call_uses_cache(self, aws_env):
        provider = AWSSecretsManagerProvider(region_name=REGION, cache_ttl_seconds=60.0)
        v1 = provider.get_secret(SECRET_NAME)

        # Sabotage the client — if cache works, this won't be called
        provider._client.get_secret_value = MagicMock(
            side_effect=Exception("should not be called")
        )
        v2 = provider.get_secret(SECRET_NAME)
        assert v2["username"] == v1["username"]

    def test_cache_expires_after_ttl(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION, cache_ttl_seconds=10.0
            )
            provider.get_secret(SECRET_NAME)

            # Advance past TTL
            time_value[0] = 200.0

            # Update the secret so we can detect a re-fetch
            aws_env.update_secret(
                SecretId=SECRET_NAME,
                SecretString=json.dumps({"username": "rotated", "password": "newpass"}),
            )
            v2 = provider.get_secret(SECRET_NAME)
            assert v2["username"] == "rotated"

    def test_cache_hit_within_ttl(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION, cache_ttl_seconds=60.0
            )
            provider.get_secret(SECRET_NAME)

            # Advance time but stay within TTL
            time_value[0] = 130.0

            # Update secret — should NOT be picked up
            aws_env.update_secret(
                SecretId=SECRET_NAME,
                SecretString=json.dumps({"username": "rotated", "password": "newpass"}),
            )
            v2 = provider.get_secret(SECRET_NAME)
            assert v2["username"] == "testuser"

    def test_ttl_recheck_inside_lock(self, aws_env):
        """When fetched_at is 0 (invalidated) at the outer check but another
        thread refreshes before we acquire the lock, the inner TTL re-check
        should return the cached value without fetching again."""
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION, cache_ttl_seconds=60.0
            )
            # Prime cache at t=100
            provider.get_secret(SECRET_NAME)

            # Simulate: outer check sees expired (t=170), but by the time
            # we re-check inside the lock, fetched_at was updated to t=165
            # by another thread (within TTL of 60s from t=170)
            entry = provider._cache[SECRET_NAME]
            entry.fetched_at = 165.0  # as if another thread just refreshed
            time_value[0] = 170.0

            # Sabotage client — should NOT be called
            provider._client.get_secret_value = MagicMock(
                side_effect=Exception("should not fetch")
            )
            secret = provider.get_secret(SECRET_NAME)
            assert secret["username"] == "testuser"


class TestStaleWhileRevalidate:
    def test_stale_value_served_on_fetch_failure(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION,
                cache_ttl_seconds=10.0,
                cache_stale_ttl_seconds=1800.0,
            )
            provider.get_secret(SECRET_NAME)

            # Advance past TTL but within stale window
            time_value[0] = 120.0

            # Make fetches fail
            provider._client.get_secret_value = MagicMock(
                side_effect=ClientError(
                    {"Error": {"Code": "InternalServiceError", "Message": "boom"}},
                    "GetSecretValue",
                )
            )
            secret = provider.get_secret(SECRET_NAME)
            assert secret["username"] == "testuser"

    def test_hard_failure_after_stale_ttl(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION,
                cache_ttl_seconds=10.0,
                cache_stale_ttl_seconds=60.0,
            )
            provider.get_secret(SECRET_NAME)

            # Advance past TTL + stale TTL
            time_value[0] = 200.0

            provider._client.get_secret_value = MagicMock(
                side_effect=ClientError(
                    {"Error": {"Code": "InternalServiceError", "Message": "boom"}},
                    "GetSecretValue",
                )
            )
            with pytest.raises(SecretProviderError, match="stale cache has expired"):
                provider.get_secret(SECRET_NAME)

    def test_no_cached_value_fetch_failure_raises(self, aws_env):
        provider = AWSSecretsManagerProvider(region_name=REGION)
        provider._client.get_secret_value = MagicMock(
            side_effect=ClientError(
                {"Error": {"Code": "InternalServiceError", "Message": "boom"}},
                "GetSecretValue",
            )
        )
        with pytest.raises(SecretProviderError, match="no cached value available"):
            provider.get_secret(SECRET_NAME)


class TestInvalidate:
    def test_invalidate_forces_refetch(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION, cache_ttl_seconds=300.0
            )
            provider.get_secret(SECRET_NAME)

            # Update secret in SM
            aws_env.update_secret(
                SecretId=SECRET_NAME,
                SecretString=json.dumps({"username": "rotated", "password": "newpass"}),
            )

            # Without invalidation, still cached
            assert provider.get_secret(SECRET_NAME)["username"] == "testuser"

            # Invalidate and re-fetch
            provider.invalidate(SECRET_NAME)
            assert provider.get_secret(SECRET_NAME)["username"] == "rotated"

    def test_invalidate_unknown_secret_is_noop(self, aws_env):
        provider = AWSSecretsManagerProvider(region_name=REGION)
        provider.invalidate("nonexistent")  # should not raise


class TestCircuitBreaker:
    def test_invalidate_within_cooldown_is_noop(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION,
                cache_ttl_seconds=10.0,
                cache_stale_ttl_seconds=1800.0,
                circuit_breaker_cooldown_seconds=30.0,
            )
            provider.get_secret(SECRET_NAME)

            # Expire TTL
            time_value[0] = 120.0

            # Make fetches fail — triggers last_failed_at
            call_count = 0
            real_get = provider._client.get_secret_value

            def counting_fail(**kwargs):
                nonlocal call_count
                call_count += 1
                raise ClientError(
                    {"Error": {"Code": "InternalServiceError", "Message": "boom"}},
                    "GetSecretValue",
                )

            provider._client.get_secret_value = counting_fail

            # First fetch after expiry — fails, serves stale, sets last_failed_at
            provider.get_secret(SECRET_NAME)
            assert call_count == 1

            # Invalidate within cooldown — should be a no-op
            provider.invalidate(SECRET_NAME)

            # Next get_secret should NOT re-fetch (circuit breaker active)
            provider.get_secret(SECRET_NAME)
            assert call_count == 1

    def test_invalidate_after_cooldown_resets(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION,
                cache_ttl_seconds=10.0,
                cache_stale_ttl_seconds=1800.0,
                circuit_breaker_cooldown_seconds=30.0,
            )
            provider.get_secret(SECRET_NAME)

            # Expire TTL, sabotage client
            time_value[0] = 120.0
            provider._client.get_secret_value = MagicMock(
                side_effect=ClientError(
                    {"Error": {"Code": "InternalServiceError", "Message": "boom"}},
                    "GetSecretValue",
                )
            )
            provider.get_secret(SECRET_NAME)  # sets last_failed_at

            # Advance past cooldown
            time_value[0] = 160.0

            # Restore client
            provider._client = boto3.client("secretsmanager", region_name=REGION)

            # Invalidate now works (past cooldown)
            provider.invalidate(SECRET_NAME)
            secret = provider.get_secret(SECRET_NAME)
            assert secret["username"] == "testuser"

    def test_circuit_resets_on_successful_ttl_refresh(self, aws_env):
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION,
                cache_ttl_seconds=10.0,
                cache_stale_ttl_seconds=1800.0,
                circuit_breaker_cooldown_seconds=30.0,
            )
            provider.get_secret(SECRET_NAME)

            # Expire TTL, fail once to set last_failed_at
            time_value[0] = 120.0
            provider._client.get_secret_value = MagicMock(
                side_effect=ClientError(
                    {"Error": {"Code": "InternalServiceError", "Message": "boom"}},
                    "GetSecretValue",
                )
            )
            provider.get_secret(SECRET_NAME)

            # Restore client, advance past both cooldown and TTL
            provider._client = boto3.client("secretsmanager", region_name=REGION)
            time_value[0] = 155.0  # past cooldown (120 + 30) and TTL expired

            # Successful fetch should clear last_failed_at
            secret = provider.get_secret(SECRET_NAME)
            assert secret["username"] == "testuser"

            # Verify circuit is reset — check the entry directly
            entry = provider._cache[SECRET_NAME]
            assert entry.last_failed_at == 0.0


class TestThreadSafety:
    def test_concurrent_invalidations_single_fetch(self, aws_env):
        """Multiple threads hitting get_secret after invalidation should
        result in only 1 actual Secrets Manager call."""
        time_value = [100.0]

        with patch(
            "fides.config.secrets.aws_secrets_manager_provider.time"
        ) as mock_time:
            mock_time.monotonic = lambda: time_value[0]

            provider = AWSSecretsManagerProvider(
                region_name=REGION, cache_ttl_seconds=300.0
            )
            provider.get_secret(SECRET_NAME)

            # Invalidate to force refetch
            provider.invalidate(SECRET_NAME)

            # Wrap client to count calls with some latency
            real_get = provider._client.get_secret_value
            call_count = 0
            call_lock = threading.Lock()

            def counting_get(**kwargs):
                nonlocal call_count
                with call_lock:
                    call_count += 1
                # Simulate latency to widen the race window
                time.sleep(0.05)
                return real_get(**kwargs)

            provider._client.get_secret_value = counting_get

            # Launch threads
            num_threads = 10
            barrier = threading.Barrier(num_threads)
            results = [None] * num_threads

            def worker(idx):
                barrier.wait()
                results[idx] = provider.get_secret(SECRET_NAME)

            threads = [
                threading.Thread(target=worker, args=(i,)) for i in range(num_threads)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Only 1 thread should have actually fetched
            assert call_count == 1, f"Expected 1 fetch, got {call_count}"
            # All threads got correct results
            assert all(r["username"] == "testuser" for r in results)
