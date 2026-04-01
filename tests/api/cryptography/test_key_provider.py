"""Tests for the cryptography.key_provider module."""

import base64
import uuid

import pytest
from sqlalchemy import create_engine, text

from fides.api.cryptography.key_provider import (
    KeyProviderError,
    LocalKeyProvider,
)

# 32-character test keys
TEST_KEK = "testkeythatisexactly32characters"
TEST_KEK_ALT = "anothertestkeythatis32characters"
TEST_DEK = "OLMkv91j8DHiDAULnK5Lxx3kSCov30b3"


@pytest.fixture()
def sqlite_engine():
    """Create an in-memory SQLite DB with the encryption_keys table."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE encryption_keys ("
                "  id TEXT PRIMARY KEY,"
                "  wrapped_dek TEXT NOT NULL,"
                "  kek_id_hash TEXT NOT NULL,"
                "  provider TEXT NOT NULL DEFAULT 'local',"
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                "  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                ")"
            )
        )
    return engine


@pytest.fixture()
def provider(sqlite_engine):
    """LocalKeyProvider backed by the in-memory SQLite DB."""
    return LocalKeyProvider(kek=TEST_KEK, engine=sqlite_engine)


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
class TestWrapUnwrap:
    def test_wrap_produces_valid_base64(self, provider):
        wrapped = provider.wrap(TEST_DEK)
        raw = base64.b64decode(wrapped)
        assert len(raw) >= 28  # nonce(12) + tag(16) + at least some ciphertext

    def test_roundtrip(self, provider):
        wrapped = provider.wrap(TEST_DEK)
        plaintext = LocalKeyProvider.unwrap_with(wrapped, TEST_KEK)
        assert plaintext == TEST_DEK

    def test_wrong_kek_raises(self, provider):
        wrapped = provider.wrap(TEST_DEK)
        with pytest.raises(KeyProviderError, match="Failed to unwrap"):
            LocalKeyProvider.unwrap_with(wrapped, TEST_KEK_ALT)

    def test_corrupt_data_raises(self):
        corrupted = base64.b64encode(b"\x00" * 40).decode()
        with pytest.raises(KeyProviderError, match="Failed to unwrap"):
            LocalKeyProvider.unwrap_with(corrupted, TEST_KEK)

    def test_short_data_raises(self):
        too_short = base64.b64encode(b"\x00" * 10).decode()
        with pytest.raises(KeyProviderError, match="too short"):
            LocalKeyProvider.unwrap_with(too_short, TEST_KEK)

    def test_invalid_base64_raises(self):
        with pytest.raises(KeyProviderError, match="Invalid base64"):
            LocalKeyProvider.unwrap_with("not-valid-base64!!!", TEST_KEK)


@pytest.mark.unit
class TestInit:
    def test_rejects_short_kek(self, sqlite_engine):
        with pytest.raises(ValueError, match="32 characters"):
            LocalKeyProvider(kek="tooshort", engine=sqlite_engine)

    def test_rejects_long_kek(self, sqlite_engine):
        with pytest.raises(ValueError, match="32 characters"):
            LocalKeyProvider(kek="a" * 64, engine=sqlite_engine)

    def test_accepts_valid_kek(self, sqlite_engine):
        provider = LocalKeyProvider(kek=TEST_KEK, engine=sqlite_engine)
        assert provider is not None


# --- DB integration tests (SQLite in-memory) ---


@pytest.mark.unit
class TestGetDek:
    def test_roundtrip_via_db(self, provider, sqlite_engine):
        """Wrap a DEK, store it, and verify get_dek() returns the original."""
        wrapped = provider.wrap(TEST_DEK)
        kek_hash = LocalKeyProvider.kek_id_hash(TEST_KEK)

        with sqlite_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO encryption_keys (id, wrapped_dek, kek_id_hash, provider) "
                    "VALUES (:id, :wrapped_dek, :kek_id_hash, :provider)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "wrapped_dek": wrapped,
                    "kek_id_hash": kek_hash,
                    "provider": "local",
                },
            )

        assert provider.get_dek() == TEST_DEK

    def test_no_row_raises(self, provider):
        """Empty table should raise KeyProviderError."""
        with pytest.raises(KeyProviderError, match="No wrapped DEK found"):
            provider.get_dek()

    def test_kek_mismatch_raises(self, provider, sqlite_engine):
        """Row wrapped with a different KEK should raise on hash mismatch."""
        alt_provider = LocalKeyProvider(kek=TEST_KEK_ALT, engine=sqlite_engine)
        wrapped = alt_provider.wrap(TEST_DEK)
        kek_hash = LocalKeyProvider.kek_id_hash(TEST_KEK_ALT)

        with sqlite_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO encryption_keys (id, wrapped_dek, kek_id_hash, provider) "
                    "VALUES (:id, :wrapped_dek, :kek_id_hash, :provider)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "wrapped_dek": wrapped,
                    "kek_id_hash": kek_hash,
                    "provider": "local",
                },
            )

        with pytest.raises(KeyProviderError, match="KEK ID mismatch"):
            provider.get_dek()
