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

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.tasks.encryption_utils import encrypt_access_request_results
from fides.api.util.cache import (
    get_cache,
    get_custom_privacy_request_field_cache_key,
    get_drp_request_body_cache_key,
    get_dsr_cache_store,
    get_encryption_cache_key,
    get_identity_cache_key,
)

_TTL = 3600  # Test TTL


@pytest.mark.unit
class TestInFlightDSRLifecycle:
    """
    Simulate a full in-flight DSR that was cached by old code, then processed
    and cleared by new code after a deployment. This is the "Steps to Confirm"
    scenario from the PR: volume of in-flight DSR processing, then upgrading
    in the middle of it.
    """

    def test_full_lifecycle_legacy_request_processed_by_new_code(self, mock_redis):
        """
        End-to-end: old code caches a complete DSR (identity, encryption,
        custom fields, DRP body). New code reads everything, processes the
        request, and clears the cache.
        """
        pr_id = f"pri_{uuid.uuid4()}"

        # --- Phase 1: "Old code" caches a full DSR using legacy key format ---
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()

            # Identity
            cache.set_with_autoexpire(
                get_identity_cache_key(pr_id, "email"), json.dumps("user@example.com")
            )
            cache.set_with_autoexpire(
                get_identity_cache_key(pr_id, "phone_number"),
                json.dumps("+1234567890"),
            )

            # Encryption key
            cache.set_with_autoexpire(
                get_encryption_cache_key(pr_id, "key"), "0123456789abcdef"
            )

            # Custom fields
            cache.set_with_autoexpire(
                get_custom_privacy_request_field_cache_key(pr_id, "department"),
                json.dumps("Engineering"),
            )
            cache.set_with_autoexpire(
                get_custom_privacy_request_field_cache_key(pr_id, "tenant_id"),
                json.dumps("tenant-42"),
            )

            # DRP body
            cache.set_with_autoexpire(
                get_drp_request_body_cache_key(pr_id, "meta"), "DrpMeta(version='0.5')"
            )
            cache.set_with_autoexpire(
                get_drp_request_body_cache_key(pr_id, "regime"), "ccpa"
            )

        # Verify legacy keys exist before "deployment"
        legacy_keys = [k for k in mock_redis.keys("*") if pr_id in k]
        assert len(legacy_keys) == 7  # 2 identity + 1 encryption + 2 custom + 2 DRP

        # --- Phase 2: "New code deployed" — read everything via PrivacyRequest ---
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            pr = MagicMock()
            pr.id = pr_id

            # Read identity (triggers migration)
            identity_data = PrivacyRequest.get_cached_identity_data(pr)
            assert identity_data["email"] == "user@example.com"
            assert identity_data["phone_number"] == "+1234567890"

            # Read encryption key (triggers migration)
            encryption_key = PrivacyRequest.get_cached_encryption_key(pr)
            assert encryption_key == "0123456789abcdef"

            # Encrypt data using the cached key
            encrypted = encrypt_access_request_results("sensitive data", pr_id)
            assert encrypted != "sensitive data"  # Actually encrypted

            # Read custom fields (triggers migration)
            store = get_dsr_cache_store(pr_id)
            custom_fields = store.get_cached_custom_fields()
            assert custom_fields["department"] == json.dumps("Engineering")
            assert custom_fields["tenant_id"] == json.dumps("tenant-42")

            # Read DRP body (triggers migration)
            drp_body = store.get_cached_drp_request_body()
            assert drp_body["meta"] == "DrpMeta(version='0.5')"
            assert drp_body["regime"] == "ccpa"

            # --- Phase 3: Verify migration happened ---
            # All legacy keys should be gone
            remaining_legacy = [
                k for k in mock_redis.keys("*") if k.startswith(f"id-{pr_id}")
            ]
            assert remaining_legacy == [], (
                f"Legacy keys not migrated: {remaining_legacy}"
            )

            # New-format keys should exist
            assert store.get_identity("email") == json.dumps("user@example.com")
            assert store.get_encryption("key") == "0123456789abcdef"

            # --- Phase 4: "Request complete" — clear the cache ---
            store.clear()

            # Everything gone
            all_keys = [k for k in mock_redis.keys("*") if pr_id in k]
            assert all_keys == [], f"Keys remain after clear: {all_keys}"

    def test_multiple_in_flight_requests_mixed_formats(self, mock_redis):
        """
        Simulate 3 concurrent requests: one fully legacy, one fully new,
        one partially migrated. All should be independently readable and
        clearable after "deployment".
        """
        legacy_id = f"pri_{uuid.uuid4()}"
        new_id = f"pri_{uuid.uuid4()}"
        mixed_id = f"pri_{uuid.uuid4()}"

        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            cache = get_cache()

            # Request 1: fully legacy
            cache.set_with_autoexpire(
                get_identity_cache_key(legacy_id, "email"),
                json.dumps("legacy@example.com"),
            )
            cache.set_with_autoexpire(
                get_encryption_cache_key(legacy_id, "key"), "legacy-key-1234567"
            )

            # Request 2: fully new format
            store_new = get_dsr_cache_store(new_id)
            store_new.write_identity("email", json.dumps("new@example.com"), _TTL)
            store_new.write_encryption("key", "new-key-123456789", _TTL)

            # Request 3: mixed (legacy identity, new encryption)
            cache.set_with_autoexpire(
                get_identity_cache_key(mixed_id, "email"),
                json.dumps("mixed@example.com"),
            )
            store_mixed = get_dsr_cache_store(mixed_id)
            store_mixed.write_encryption("key", "mixed-key-12345678", _TTL)

        # --- "New code deployed" — read all three ---
        with (
            patch("fides.api.util.cache.get_cache", return_value=mock_redis),
            patch("fides.api.util.cache._connection", mock_redis),
        ):
            for pr_id, expected_email, expected_key in [
                (legacy_id, "legacy@example.com", "legacy-key-1234567"),
                (new_id, "new@example.com", "new-key-123456789"),
                (mixed_id, "mixed@example.com", "mixed-key-12345678"),
            ]:
                pr = MagicMock()
                pr.id = pr_id
                identity = PrivacyRequest.get_cached_identity_data(pr)
                assert identity["email"] == expected_email, f"Failed for {pr_id}"
                enc_key = PrivacyRequest.get_cached_encryption_key(pr)
                assert enc_key == expected_key, f"Failed for {pr_id}"

            # Clear one, others unaffected
            store_legacy = get_dsr_cache_store(legacy_id)
            store_legacy.clear()

            pr_new = MagicMock()
            pr_new.id = new_id
            assert (
                PrivacyRequest.get_cached_identity_data(pr_new)["email"]
                == "new@example.com"
            )

            pr_mixed = MagicMock()
            pr_mixed.id = mixed_id
            assert (
                PrivacyRequest.get_cached_identity_data(pr_mixed)["email"]
                == "mixed@example.com"
            )

            # Legacy request fully cleared
            assert store_legacy.get_all_keys() == []
