"""
Production compatibility tests for DSR cache migration.

These tests simulate a production deployment scenario where:
1. Old code has cached DSR data using legacy key formats (id-{id}-*)
2. New code is deployed and must read/process those in-flight requests
3. New code continues to work correctly with legacy keys

This validates that the migration won't break production requests that are
already in-flight when the new code is deployed.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

# PrivacyRequest imported inside tests to ensure get_cache is patched
from fides.api.schemas.redis_cache import Identity
from fides.api.util.cache import (
    FidesopsRedis,
    get_cache,
    get_drp_request_body_cache_key,
    get_encryption_cache_key,
    get_identity_cache_key,
)
from fides.common.cache.dsr_store import DSRCacheStore
from fides.common.cache.manager import RedisCacheManager
from tests.common.cache.mock_redis import MockRedis


@pytest.fixture
def mock_redis():
    """Shared MockRedis instance."""
    return MockRedis()


@pytest.fixture
def pr_id():
    """Generate unique privacy request ID."""
    return f"pri_{uuid.uuid4()}"


@pytest.mark.unit
class TestProductionCompatibilityLegacyKeys:
    """
    Test that new code can read and process privacy requests that were
    cached by old code using legacy key formats.
    """

    def simulate_legacy_cache_write(
        self, cache: FidesopsRedis, pr_id: str, identity: Identity, encryption_key: str
    ) -> None:
        """
        Simulate how old code would cache data - using direct cache.set_with_autoexpire
        with legacy key formats.
        """
        # Legacy identity caching
        identity_dict = identity.labeled_dict()
        for key, value in identity_dict.items():
            if value is not None:
                if isinstance(value, dict):
                    # LabeledIdentity - encode as JSON
                    cache.set_with_autoexpire(
                        get_identity_cache_key(pr_id, key), json.dumps(value)
                    )
                else:
                    cache.set_with_autoexpire(get_identity_cache_key(pr_id, key), value)

        # Legacy encryption key caching
        cache.set_with_autoexpire(
            get_encryption_cache_key(pr_id, "key"), encryption_key
        )

    def test_privacy_request_reads_legacy_identity_during_processing(
        self, mock_redis, pr_id
    ):
        """
        Production scenario: Privacy request was created and cached by old code.
        New code reads identity during request processing.
        """
        # Simulate old code caching identity
        identity = Identity(email="user@example.com", phone_number="+1234567890")
        encryption_key = "test-encryption-key-12345"

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            self.simulate_legacy_cache_write(cache, pr_id, identity, encryption_key)

            # Simulate PrivacyRequest instance (minimal mock)
            pr = MagicMock()
            pr.id = pr_id

            # Import PrivacyRequest inside patch context
            from fides.api.models.privacy_request import PrivacyRequest

            # New code reads cached identity - must be within patch context
            identity_data = PrivacyRequest.get_cached_identity_data(pr)

            # Should successfully read from legacy keys
            assert identity_data["email"] == "user@example.com"
            assert identity_data["phone_number"] == "+1234567890"

            # Legacy keys should be migrated to new format
            from fides.api.util.cache import get_dsr_cache_store

            with get_dsr_cache_store() as store:
                assert store.get_identity(pr_id, "email") == "user@example.com"
                # Legacy key should be deleted after migration
                assert mock_redis.get(get_identity_cache_key(pr_id, "email")) is None

    def test_privacy_request_reads_legacy_encryption_during_processing(
        self, mock_redis, pr_id
    ):
        """
        Production scenario: Encryption key was cached by old code.
        New code reads encryption key during request processing.
        """
        encryption_key = "legacy-encryption-key-16b"  # 16 bytes

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            cache.set_with_autoexpire(
                get_encryption_cache_key(pr_id, "key"), encryption_key
            )

            # Import PrivacyRequest inside patch context
            from fides.api.models.privacy_request import PrivacyRequest

            # New code reads encryption key
            pr = MagicMock()
            pr.id = pr_id
            cached_key = PrivacyRequest.get_cached_encryption_key(pr)

            assert cached_key == encryption_key

            # Legacy key should be migrated
            from fides.api.util.cache import get_dsr_cache_store

            with get_dsr_cache_store() as store:
                assert store.get_encryption(pr_id, "key") == encryption_key
                assert mock_redis.get(get_encryption_cache_key(pr_id, "key")) is None

    def test_encryption_utils_reads_legacy_encryption_key(self, mock_redis, pr_id):
        """
        Production scenario: Encryption key cached by old code.
        encrypt_access_request_results reads it during processing.
        """
        encryption_key = "0123456789abcdef"  # 16 bytes
        test_data = "sensitive data to encrypt"

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            cache.set_with_autoexpire(
                get_encryption_cache_key(pr_id, "key"), encryption_key
            )

            # New code encrypts data using cached key
            from fides.api.tasks.encryption_utils import encrypt_access_request_results

            encrypted = encrypt_access_request_results(test_data, pr_id)

            # Should successfully encrypt (result is base64 string)
            assert isinstance(encrypted, str)
            assert len(encrypted) > 0
            assert encrypted != test_data  # Should be encrypted, not plaintext

    def test_mixed_legacy_and_new_keys_same_request(self, mock_redis, pr_id):
        """
        Production scenario: Some fields cached by old code, some by new code
        (e.g., request started before deployment, continued after).
        """
        # Old code cached identity
        identity = Identity(email="legacy@example.com")
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            cache.set_with_autoexpire(
                get_identity_cache_key(pr_id, "email"), identity.email
            )

        # New code caches encryption
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.util.cache import get_dsr_cache_store

            with get_dsr_cache_store() as store:
                store.write_encryption(pr_id, "key", "new-encryption-key")

        # Both should be readable
        pr = MagicMock()
        pr.id = pr_id

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.models.privacy_request import PrivacyRequest

            # get_cached_identity_data should find and migrate the legacy key
            identity_data = PrivacyRequest.get_cached_identity_data(pr)
            # After migration, the data should be available in the returned dict
            assert identity_data["email"] == "legacy@example.com"

            encryption_key = PrivacyRequest.get_cached_encryption_key(pr)
            assert encryption_key == "new-encryption-key"

            # Verify migration happened - legacy key should be deleted
            assert mock_redis.get(get_identity_cache_key(pr_id, "email")) is None

    def test_legacy_drp_request_body_readable(self, mock_redis, pr_id):
        """
        Production scenario: DRP request body cached by old code.
        New code reads it during processing.
        """
        # Simulate old code caching DRP body
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            cache.set_with_autoexpire(
                get_drp_request_body_cache_key(pr_id, "meta"),
                "DrpMeta(version='0.5')",
            )
            cache.set_with_autoexpire(
                get_drp_request_body_cache_key(pr_id, "regime"), "ccpa"
            )

        # New code reads DRP body
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.util.cache import get_dsr_cache_store

            with get_dsr_cache_store() as store:
                meta = store.get_drp(pr_id, "meta")
                regime = store.get_drp(pr_id, "regime")

                assert meta == "DrpMeta(version='0.5')"
                assert regime == "ccpa"

                # Legacy keys should be migrated
                assert (
                    mock_redis.get(get_drp_request_body_cache_key(pr_id, "meta"))
                    is None
                )

    def test_legacy_custom_fields_readable(self, mock_redis, pr_id):
        """
        Production scenario: Custom fields cached by old code.
        New code reads them during processing.
        """
        from fides.api.util.cache import (
            get_custom_privacy_request_field_cache_key,
        )

        # Simulate old code caching custom fields
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            cache.set_with_autoexpire(
                get_custom_privacy_request_field_cache_key(pr_id, "department"),
                json.dumps("Engineering"),
            )

        # New code reads custom fields
        pr = MagicMock()
        pr.id = pr_id

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.models.privacy_request import PrivacyRequest

            custom_fields = PrivacyRequest.get_cached_custom_privacy_request_fields(pr)

            assert custom_fields["department"] == "Engineering"

    def test_concurrent_legacy_and_new_requests(self, mock_redis):
        """
        Production scenario: Multiple requests in flight - some with legacy keys,
        some with new keys. Verify isolation and correct reads.
        """
        pr1_id = f"pri_{uuid.uuid4()}"
        pr2_id = f"pri_{uuid.uuid4()}"

        # PR1: cached by old code (legacy keys)
        identity1 = Identity(email="legacy1@example.com")
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            cache.set_with_autoexpire(
                get_identity_cache_key(pr1_id, "email"), identity1.email
            )

        # PR2: cached by new code (new keys)
        identity2 = Identity(email="new2@example.com")
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.util.cache import get_dsr_cache_store

            with get_dsr_cache_store() as store:
                store.cache_identity_data(
                    pr2_id,
                    {"email": identity2.email},
                    expire_seconds=3600,
                )

        # Both should be readable correctly
        pr1 = MagicMock()
        pr1.id = pr1_id
        pr2 = MagicMock()
        pr2.id = pr2_id

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.models.privacy_request import PrivacyRequest

            data1 = PrivacyRequest.get_cached_identity_data(pr1)
            data2 = PrivacyRequest.get_cached_identity_data(pr2)

            assert data1["email"] == "legacy1@example.com"
            assert data2["email"] == "new2@example.com"

    def test_legacy_keys_migrated_on_first_read_not_on_write(self, mock_redis, pr_id):
        """
        Production scenario: Legacy keys exist. New code writes additional data.
        Legacy keys should only migrate on read, not interfere with new writes.
        """
        # Old code cached identity
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()
            cache.set_with_autoexpire(
                get_identity_cache_key(pr_id, "email"), "legacy@example.com"
            )

        # New code writes encryption (shouldn't trigger migration)
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.util.cache import get_dsr_cache_store

            with get_dsr_cache_store() as store:
                store.write_encryption(pr_id, "key", "new-key")

        # Legacy identity key should still exist (not migrated yet)
        assert (
            mock_redis.get(get_identity_cache_key(pr_id, "email"))
            == "legacy@example.com"
        )

        # Reading identity should trigger migration
        pr = MagicMock()
        pr.id = pr_id

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            from fides.api.models.privacy_request import PrivacyRequest
            from fides.api.util.cache import get_dsr_cache_store

            # get_cached_identity_data calls get_identity which should trigger migration
            PrivacyRequest.get_cached_identity_data(pr)

            # Verify migration happened by checking the store directly
            with get_dsr_cache_store() as store:
                # The new key should exist
                assert store.get_identity(pr_id, "email") == "legacy@example.com"

        # Now legacy key should be migrated (deleted)
        assert mock_redis.get(get_identity_cache_key(pr_id, "email")) is None

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            with get_dsr_cache_store() as store:
                assert store.get_identity(pr_id, "email") == "legacy@example.com"
