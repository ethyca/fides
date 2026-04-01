"""Tests for the cryptography.key_providers module."""

import base64

import pytest
from sqlalchemy import text

from fides.api.cryptography.key_providers import KeyProviderError, LocalKeyProvider
from fides.api.models.encryption_key import EncryptionKey

# 32-character test keys
TEST_KEK = "testkeythatisexactly32characters"
TEST_KEK_ALT = "anothertestkeythatis32characters"
TEST_DEK = "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"


# --- Pure crypto tests (no DB) ---


@pytest.mark.unit
class TestKekIdHash:
    def test_deterministic(self):
        h1 = LocalKeyProvider.kek_id_hash(TEST_KEK)
        h2 = LocalKeyProvider.kek_id_hash(TEST_KEK)
        assert h1 == h2

    def test_different_keys_produce_different_hashes(self):
        h1 = LocalKeyProvider.kek_id_hash(TEST_KEK)
        h2 = LocalKeyProvider.kek_id_hash(TEST_KEK_ALT)
        assert h1 != h2

    def test_length_is_16_hex_chars(self):
        h = LocalKeyProvider.kek_id_hash(TEST_KEK)
        assert len(h) == 16
        int(h, 16)  # valid hex


@pytest.mark.unit
class TestEncryptDecrypt:
    def test_encrypt_produces_valid_base64(self, db):
        provider = LocalKeyProvider(kek=TEST_KEK, session=db)
        encrypted = provider.encrypt_dek(TEST_DEK)
        raw = base64.b64decode(encrypted)
        assert len(raw) >= 28  # nonce(12) + tag(16) + at least some ciphertext

    def test_roundtrip(self, db):
        provider = LocalKeyProvider(kek=TEST_KEK, session=db)
        encrypted = provider.encrypt_dek(TEST_DEK)
        plaintext = LocalKeyProvider.decrypt_with(encrypted, TEST_KEK)
        assert plaintext == TEST_DEK

    def test_wrong_kek_raises(self, db):
        provider = LocalKeyProvider(kek=TEST_KEK, session=db)
        encrypted = provider.encrypt_dek(TEST_DEK)
        with pytest.raises(KeyProviderError, match="Failed to unwrap"):
            LocalKeyProvider.decrypt_with(encrypted, TEST_KEK_ALT)

    def test_corrupt_data_raises(self):
        corrupted = base64.b64encode(b"\x00" * 40).decode()
        with pytest.raises(KeyProviderError, match="Failed to unwrap"):
            LocalKeyProvider.decrypt_with(corrupted, TEST_KEK)

    def test_short_data_raises(self):
        too_short = base64.b64encode(b"\x00" * 10).decode()
        with pytest.raises(KeyProviderError, match="too short"):
            LocalKeyProvider.decrypt_with(too_short, TEST_KEK)

    def test_invalid_base64_raises(self):
        with pytest.raises(KeyProviderError, match="Invalid base64"):
            LocalKeyProvider.decrypt_with("not-valid-base64!!!", TEST_KEK)


# --- DB integration tests ---


@pytest.fixture(autouse=False)
def clean_encryption_keys(db):
    """Clean up encryption_keys table after each test that uses it."""
    yield
    db.execute(text("DELETE FROM encryption_keys"))
    db.commit()


class TestGetDek:
    def test_roundtrip_via_db(self, db, clean_encryption_keys):
        """Encrypt a DEK, store it, and verify get_dek() returns the original."""
        provider = LocalKeyProvider(kek=TEST_KEK, session=db)
        encrypted = provider.encrypt_dek(TEST_DEK)

        row = EncryptionKey(
            wrapped_dek=encrypted,
            kek_id_hash=LocalKeyProvider.kek_id_hash(TEST_KEK),
            provider="local",
        )
        db.add(row)
        db.flush()

        assert provider.get_dek() == TEST_DEK

    def test_no_row_raises(self, db, clean_encryption_keys):
        """Empty table should raise KeyProviderError."""
        provider = LocalKeyProvider(kek=TEST_KEK, session=db)
        with pytest.raises(KeyProviderError, match="No wrapped DEK found"):
            provider.get_dek()

    def test_kek_mismatch_raises(self, db, clean_encryption_keys):
        """Row encrypted with a different KEK should raise on hash mismatch."""
        alt_provider = LocalKeyProvider(kek=TEST_KEK_ALT, session=db)
        encrypted = alt_provider.encrypt_dek(TEST_DEK)

        row = EncryptionKey(
            wrapped_dek=encrypted,
            kek_id_hash=LocalKeyProvider.kek_id_hash(TEST_KEK_ALT),
            provider="local",
        )
        db.add(row)
        db.flush()

        provider = LocalKeyProvider(kek=TEST_KEK, session=db)
        with pytest.raises(KeyProviderError, match="KEK ID mismatch"):
            provider.get_dek()
