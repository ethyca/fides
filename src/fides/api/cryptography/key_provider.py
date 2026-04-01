"""Key provider abstraction for envelope encryption.

Defines the KeyProvider ABC and the LocalKeyProvider implementation that
wraps/unwraps the Data Encryption Key (DEK) using AES-256-GCM with a
Key Encryption Key (KEK) stored in config.
"""

import base64
import hashlib
import hmac
import os
from abc import ABC, abstractmethod

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from sqlalchemy import text
from sqlalchemy.engine import Engine


class KeyProviderError(Exception):
    """Raised when a key provider operation fails."""


class KeyProvider(ABC):
    """Abstract base class for envelope encryption key providers."""

    @abstractmethod
    def get_dek(self) -> str:
        """Retrieve and unwrap the Data Encryption Key."""
        ...

    @abstractmethod
    def wrap(self, dek: str) -> str:
        """Wrap (encrypt) a DEK for storage.

        Returns the wrapped DEK as a base64-encoded string.
        """
        ...


class LocalKeyProvider(KeyProvider):
    """Envelope encryption provider using in-process AES-256-GCM.

    The KEK is supplied at construction time (from config). The wrapped DEK
    is stored in the ``encryption_keys`` database table.
    """

    def __init__(self, kek: str, engine: Engine) -> None:
        if len(kek.encode("UTF-8")) != 32:
            raise ValueError("KEK must be exactly 32 characters (32 bytes in UTF-8)")
        self._kek = kek
        self._engine = engine

    @staticmethod
    def kek_id_hash(kek: str) -> str:
        """Compute a truncated HMAC that identifies a KEK without leaking it.

        Uses a fixed domain-separation key so the hash is deterministic
        for a given KEK but reveals nothing about the key material.
        """
        digest = hmac.new(
            key=b"fides-kek-id",
            msg=kek.encode("UTF-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        return digest[:16]

    def wrap(self, dek: str) -> str:
        """Wrap a DEK with the configured KEK using AES-256-GCM.

        Returns ``base64(nonce[12] + tag[16] + ciphertext)``.
        """
        nonce = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(self._kek.encode("UTF-8")),
            modes.GCM(nonce),
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(dek.encode("UTF-8")) + encryptor.finalize()
        return base64.b64encode(nonce + encryptor.tag + ciphertext).decode("UTF-8")

    @staticmethod
    def unwrap_with(wrapped_dek: str, kek: str) -> str:
        """Unwrap a DEK using the given KEK.

        This is public so that KEK rotation (PR 7) can unwrap with the
        previous KEK before re-wrapping with the new one.
        """
        try:
            raw = base64.b64decode(wrapped_dek)
        except Exception as exc:
            raise KeyProviderError("Invalid base64 in wrapped DEK") from exc

        if len(raw) < 28:
            raise KeyProviderError(
                "Wrapped DEK too short — expected at least 28 bytes (12 nonce + 16 tag)"
            )

        nonce, tag, ciphertext = raw[:12], raw[12:28], raw[28:]
        try:
            cipher = Cipher(
                algorithms.AES(kek.encode("UTF-8")),
                modes.GCM(nonce, tag),
            )
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode("UTF-8")
        except Exception as exc:
            raise KeyProviderError(
                "Failed to unwrap DEK — the KEK may be incorrect or the "
                "wrapped DEK may be corrupt"
            ) from exc

    def get_dek(self) -> str:
        """Read the wrapped DEK from the database and unwrap it."""
        with self._engine.connect() as connection:
            result = connection.execute(
                text(
                    "SELECT wrapped_dek, kek_id_hash "
                    "FROM encryption_keys "
                    "WHERE provider = :provider "
                    "ORDER BY created_at DESC LIMIT 1"
                ),
                {"provider": "local"},
            )
            row = result.fetchone()

        if row is None:
            raise KeyProviderError(
                "No wrapped DEK found in encryption_keys table. "
                "Bootstrap has not run yet."
            )

        row_mapping = row._mapping
        wrapped_dek = row_mapping["wrapped_dek"]
        stored_hash = row_mapping["kek_id_hash"]
        expected_hash = self.kek_id_hash(self._kek)

        if stored_hash != expected_hash:
            raise KeyProviderError(
                f"KEK ID mismatch: expected {expected_hash}, found {stored_hash}. "
                "The KEK may have been rotated — set key_encryption_key_previous "
                "to the old KEK and restart."
            )

        return self.unwrap_with(wrapped_dek, self._kek)
