"""Tests for consent_encryption_migration utility."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.util.consent_encryption_migration import migrate_consent_encryption


class TestMigrateConsentEncryption:
    @pytest.fixture(autouse=True)
    def _insert_test_row(self, db: Session):
        """Insert a plaintext test row and clean up after each test."""
        row_id = db.execute(
            text(
                "INSERT INTO privacy_preferences "
                "(is_latest, record_data) "
                "VALUES (true, :data) "
                "RETURNING id"
            ),
            {"data": "test_plaintext_value"},
        ).scalar()
        db.commit()
        self.row_id = row_id
        yield
        db.execute(
            text("DELETE FROM privacy_preferences WHERE id = :id AND is_latest = true"),
            {"id": self.row_id},
        )
        db.commit()

    def _read_record(self, db: Session) -> str:
        return db.execute(
            text(
                "SELECT record_data FROM privacy_preferences "
                "WHERE id = :id AND is_latest = true"
            ),
            {"id": self.row_id},
        ).scalar()

    def test_invalid_direction_raises(self, db: Session) -> None:
        with pytest.raises(
            ValueError, match='direction must be "encrypt" or "decrypt"'
        ):
            migrate_consent_encryption(db, direction="invalid")

    def test_empty_table_after_cleanup(self, db: Session) -> None:
        """When no matching rows exist, total_processed is 0."""
        db.execute(
            text("DELETE FROM privacy_preferences WHERE id = :id AND is_latest = true"),
            {"id": self.row_id},
        )
        db.commit()

        result = migrate_consent_encryption(db, direction="decrypt", batch_size=5)
        assert result.batches == 0
        assert result.success

        # Re-insert so autouse teardown doesn't fail
        self.row_id = db.execute(
            text(
                "INSERT INTO privacy_preferences "
                "(is_latest, record_data) "
                "VALUES (true, :data) "
                "RETURNING id"
            ),
            {"data": "test_plaintext_value"},
        ).scalar()
        db.commit()

    def test_encrypt_decrypt_roundtrip(self, db: Session) -> None:
        """Encrypt then decrypt round-trip restores the original plaintext."""
        result_enc = migrate_consent_encryption(db, direction="encrypt", batch_size=10)
        assert result_enc.total_processed >= 1

        result_dec = migrate_consent_encryption(db, direction="decrypt", batch_size=10)
        assert result_dec.total_processed >= 1

        assert self._read_record(db) == "test_plaintext_value"

    def test_encrypt_is_idempotent(self, db: Session) -> None:
        """Running encrypt twice does not double-encrypt."""
        migrate_consent_encryption(db, direction="encrypt", batch_size=10)
        ciphertext_after_first = self._read_record(db)

        migrate_consent_encryption(db, direction="encrypt", batch_size=10)
        ciphertext_after_second = self._read_record(db)

        assert ciphertext_after_first == ciphertext_after_second

        migrate_consent_encryption(db, direction="decrypt", batch_size=10)
        assert self._read_record(db) == "test_plaintext_value"

    def test_decrypt_is_idempotent(self, db: Session) -> None:
        """Running decrypt twice does not raise or corrupt already-plaintext data."""
        migrate_consent_encryption(db, direction="encrypt", batch_size=10)
        migrate_consent_encryption(db, direction="decrypt", batch_size=10)
        plaintext_after_first = self._read_record(db)
        assert plaintext_after_first == "test_plaintext_value"

        result = migrate_consent_encryption(db, direction="decrypt", batch_size=10)
        plaintext_after_second = self._read_record(db)

        assert result.success
        assert plaintext_after_first == plaintext_after_second

    def test_batching_multiple_batches(self, db: Session) -> None:
        """Multiple batches are processed when row count exceeds batch_size."""
        extra_ids = []
        for i in range(4):
            row_id = db.execute(
                text(
                    "INSERT INTO privacy_preferences "
                    "(is_latest, record_data) "
                    "VALUES (true, :data) "
                    "RETURNING id"
                ),
                {"data": f"batch_test_{i}"},
            ).scalar()
            extra_ids.append(row_id)
        db.commit()

        try:
            # 5 total rows (1 from autouse + 4 extra), batch_size=2 → at least 3 batches
            result = migrate_consent_encryption(db, direction="encrypt", batch_size=2)
            assert result.batches >= 3
            assert result.total_processed >= 5
        finally:
            migrate_consent_encryption(db, direction="decrypt", batch_size=10)
            for eid in extra_ids:
                db.execute(
                    text(
                        "DELETE FROM privacy_preferences "
                        "WHERE id = :id AND is_latest = true"
                    ),
                    {"id": eid},
                )
            db.commit()

    def test_progress_callback_invoked(self, db: Session) -> None:
        """Progress callback is called after each batch."""
        progress_calls = []

        def on_progress(total: int, batch_num: int) -> None:
            progress_calls.append((total, batch_num))

        migrate_consent_encryption(
            db,
            direction="encrypt",
            batch_size=5,
            progress_callback=on_progress,
        )

        assert len(progress_calls) >= 1
        assert progress_calls[0][0] >= 1  # total_processed
        assert progress_calls[0][1] == 1  # first batch

        # Clean up: decrypt back so the fixture teardown finds the original value
        migrate_consent_encryption(db, direction="decrypt", batch_size=10)
