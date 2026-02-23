"""
Tests that KeyMapper maps legacy key patterns to the new dsr:{id}:{part} format correctly.
No Redis required; exercises fides.common.cache.key_mapping only.
"""

import pytest

from fides.common.cache.key_mapping import DSR_KEY_PREFIX, KeyMapper


@pytest.mark.unit
class TestKeyMapper:
    """Ensure each field type produces the expected new_key and legacy_key."""

    def test_identity(self) -> None:
        new_key, legacy_key = KeyMapper.identity("pr-123", "email")
        assert new_key == f"{DSR_KEY_PREFIX}pr-123:identity:email"
        assert legacy_key == "id-pr-123-identity-email"

    def test_custom_field(self) -> None:
        new_key, legacy_key = KeyMapper.custom_field("pr-456", "my_field")
        assert new_key == f"{DSR_KEY_PREFIX}pr-456:custom_field:my_field"
        assert legacy_key == "id-pr-456-custom-privacy-request-field-my_field"

    def test_drp(self) -> None:
        new_key, legacy_key = KeyMapper.drp("pr-789", "address")
        assert new_key == f"{DSR_KEY_PREFIX}pr-789:drp:address"
        assert legacy_key == "id-pr-789-drp-address"

    def test_encryption(self) -> None:
        new_key, legacy_key = KeyMapper.encryption("pr-abc", "key")
        assert new_key == f"{DSR_KEY_PREFIX}pr-abc:encryption:key"
        assert legacy_key == "id-pr-abc-encryption-key"

    def test_masking_secret(self) -> None:
        new_key, legacy_key = KeyMapper.masking_secret(
            "pr-def", "hash", "salt"
        )
        assert new_key == f"{DSR_KEY_PREFIX}pr-def:masking_secret:hash:salt"
        assert legacy_key == "id-pr-def-masking-secret-hash-salt"

    def test_async_execution(self) -> None:
        new_key, legacy_key = KeyMapper.async_execution("pr-ghi")
        assert new_key == f"{DSR_KEY_PREFIX}pr-ghi:async_execution"
        assert legacy_key == "id-pr-ghi-async-execution"

    def test_retry_count(self) -> None:
        new_key, legacy_key = KeyMapper.retry_count("pr-jkl")
        assert new_key == f"{DSR_KEY_PREFIX}pr-jkl:retry_count"
        assert legacy_key == "id-pr-jkl-privacy-request-retry-count"

    def test_webhook_manual_access(self) -> None:
        new_key, legacy_key = KeyMapper.webhook_manual_access(
            "pr-mno", "webhook-uuid"
        )
        assert new_key == f"{DSR_KEY_PREFIX}pr-mno:webhook_manual_access:webhook-uuid"
        assert legacy_key == "WEBHOOK_MANUAL_ACCESS_INPUT__pr-mno__webhook-uuid"

    def test_webhook_manual_erasure(self) -> None:
        new_key, legacy_key = KeyMapper.webhook_manual_erasure(
            "pr-pqr", "webhook-uuid-2"
        )
        assert new_key == f"{DSR_KEY_PREFIX}pr-pqr:webhook_manual_erasure:webhook-uuid-2"
        assert legacy_key == "WEBHOOK_MANUAL_ERASURE_INPUT__pr-pqr__webhook-uuid-2"

    def test_data_use_map(self) -> None:
        new_key, legacy_key = KeyMapper.data_use_map("pr-stu")
        assert new_key == f"{DSR_KEY_PREFIX}pr-stu:data_use_map"
        assert legacy_key == "DATA_USE_MAP__pr-stu"

    def test_email_info(self) -> None:
        new_key, legacy_key = KeyMapper.email_info(
            "pr-vwx", "access", "postgres_example", "address"
        )
        assert new_key == f"{DSR_KEY_PREFIX}pr-vwx:email_info:access:postgres_example:address"
        assert legacy_key == "EMAIL_INFORMATION__pr-vwx__access__postgres_example__address"

    def test_paused_location(self) -> None:
        new_key, legacy_key = KeyMapper.paused_location("pr-yz1")
        assert new_key == f"{DSR_KEY_PREFIX}pr-yz1:paused_location"
        assert legacy_key == "PAUSED_LOCATION__pr-yz1"

    def test_failed_location(self) -> None:
        new_key, legacy_key = KeyMapper.failed_location("pr-yz2")
        assert new_key == f"{DSR_KEY_PREFIX}pr-yz2:failed_location"
        assert legacy_key == "FAILED_LOCATION__pr-yz2"

    def test_access_request(self) -> None:
        new_key, legacy_key = KeyMapper.access_request(
            "pr-yz3", "access_request__postgres_example:address"
        )
        assert new_key == f"{DSR_KEY_PREFIX}pr-yz3:access_request:access_request__postgres_example:address"
        assert legacy_key == "pr-yz3__access_request__postgres_example:address"

    def test_erasure_request(self) -> None:
        new_key, legacy_key = KeyMapper.erasure_request(
            "pr-yz4", "postgres_example:address"
        )
        assert new_key == f"{DSR_KEY_PREFIX}pr-yz4:erasure_request:postgres_example:address"
        assert legacy_key == "pr-yz4__erasure_request__postgres_example:address"

    def test_placeholder_results(self) -> None:
        new_key, legacy_key = KeyMapper.placeholder_results(
            "pr-yz5", "postgres_example:customer"
        )
        assert new_key == f"{DSR_KEY_PREFIX}pr-yz5:placeholder_results:postgres_example:customer"
        assert legacy_key == "PLACEHOLDER_RESULTS__pr-yz5__postgres_example:customer"

    def test_index_prefix(self) -> None:
        prefix = KeyMapper.index_prefix("pr-123")
        assert prefix == "__idx:dsr:pr-123"
