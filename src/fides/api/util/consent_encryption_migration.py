"""
Utility for migrating v3 privacy_preferences record_data between encrypted and plaintext.

Used by the CLI command `fides db migrate-consent-encryption` so users can transform
data before toggling FIDES__CONSENT__CONSENT_V3_ENCRYPTION_ENABLED.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from sqlalchemy import Text, text
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.config import CONFIG

SELECT_QUERY = text(
    """
    SELECT id, is_latest, record_data
    FROM privacy_preferences
    WHERE record_data IS NOT NULL
    ORDER BY id
    LIMIT :batch_size OFFSET :offset
    """
)

UPDATE_QUERY = text(
    """
    UPDATE privacy_preferences
    SET record_data = :record_data, is_encrypted = :is_encrypted
    WHERE id = :id AND is_latest = :is_latest
    """
)


@dataclass
class MigrationResult:
    """Result of a consent encryption migration run."""

    total_processed: int = 0
    batches: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def _make_encryptor() -> StringEncryptedType:
    """Build the encryptor used for transform (encrypt/decrypt)."""
    return StringEncryptedType(
        type_in=Text(),
        key=CONFIG.security.app_encryption_key,
        engine=AesGcmEngine,
        padding="pkcs5",
    )


def _is_encrypted(encryptor: StringEncryptedType, value: str) -> bool:
    """
    Return True if value is valid ciphertext, False if it appears to be plaintext.

    Uses a trial decrypt; any failure means the value is not valid ciphertext.
    The decrypt path can fail in several ways (InvalidCiphertextError,
    binascii.Error, cryptography.exceptions.InvalidTag, etc.) so we catch
    broadly here.
    """
    try:
        encryptor.process_result_value(value, dialect="")
        return True
    except Exception:  # noqa: BLE001 - intentional broad catch for trial decrypt
        return False


def _transform_value(
    encryptor: StringEncryptedType, raw: str, direction: str
) -> Optional[str]:
    """
    Transform one record_data value, or return None if already in the target state.

    - encrypt: skips rows that are already encrypted.
    - decrypt: skips rows that are already plaintext.
    """
    already_encrypted = _is_encrypted(encryptor, raw)

    if direction == "encrypt":
        if already_encrypted:
            return None  # already encrypted, nothing to do
        return encryptor.process_bind_param(raw, dialect="")

    # direction == "decrypt"
    if not already_encrypted:
        return None  # already plaintext, nothing to do
    return encryptor.process_result_value(raw, dialect="")


def _process_batch(
    db: Session,
    encryptor: StringEncryptedType,
    direction: str,
    rows: list,
) -> None:
    """Transform and write back one batch of rows; caller commits."""
    for row in rows:
        if row.record_data is None:
            continue
        transformed = _transform_value(encryptor, row.record_data, direction)
        if transformed is None:
            continue  # row already in the target state, skip UPDATE
        db.execute(
            UPDATE_QUERY,
            {
                "record_data": transformed,
                "is_encrypted": direction == "encrypt",
                "id": row.id,
                "is_latest": row.is_latest,
            },
        )


def migrate_consent_encryption(
    db: Session,
    direction: str,
    batch_size: int = 5000,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> MigrationResult:
    """
    Encrypt or decrypt all record_data in the v3 privacy_preferences table.
    Warning: This script is not meant for production use.

    Uses raw SQL to avoid ORM column type auto-transformation. Processes rows
    in batches and commits after each batch.

    Args:
        db: Database session (caller manages lifecycle).
        direction: "encrypt" or "decrypt".
        batch_size: Number of rows to process per batch.
        progress_callback: Optional callback(total_processed, batch_num) after each batch.

    Returns:
        MigrationResult with total_processed, batches, and any errors.
    """
    if not CONFIG.dev_mode:
        raise ValueError(
            "Dev mode is disabled -- this script is not meant for production use."
        )

    if direction not in ("encrypt", "decrypt"):
        raise ValueError('direction must be "encrypt" or "decrypt"')

    encryptor = _make_encryptor()
    result = MigrationResult()
    offset = 0

    while True:
        rows = db.execute(
            SELECT_QUERY,
            {"batch_size": batch_size, "offset": offset},
        ).fetchall()

        if not rows:
            break

        result.batches += 1
        try:
            _process_batch(db, encryptor, direction, rows)
            db.commit()
            result.total_processed += len(rows)
            if progress_callback:
                progress_callback(result.total_processed, result.batches)
        except Exception as e:
            db.rollback()
            result.errors.append(f"Batch {result.batches} (offset {offset}): {e!s}")
            raise

        if len(rows) < batch_size:
            break
        offset += batch_size

    return result
