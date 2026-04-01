"""Local envelope encryption provider using in-process AES-256-GCM."""

import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from sqlalchemy.orm import Session

from fides.api.models.encryption_key import EncryptionKey

from .base_provider import KeyProvider, KeyProviderError


class LocalKeyProvider(KeyProvider):
    """Envelope encryption provider using in-process AES-256-GCM.

    The KEK is supplied at construction time (from config). The wrapped DEK
    is stored in the encryption_keys database table.
    """

    def __init__(self, kek: str, session: Session) -> None:
        self._kek = kek
        self._session = session

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

    def encrypt_dek(self, dek: str) -> str:
        """Encrypt a DEK with the configured KEK using AES-256-GCM.

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
    def decrypt_with(wrapped_dek: str, kek: str) -> str:
        """Unwrap a DEK using the given KEK.

        This is public so that KEK rotation can unwrap with the previous
        KEK before re-wrapping with the new one.
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
        """Read the wrapped DEK from the database and decrypt it."""
        row = EncryptionKey.get_by_provider(self._session, provider="local")

        if row is None:
            raise KeyProviderError(
                "No wrapped DEK found in encryption_keys table. "
                "Bootstrap has not run yet."
            )

        wrapped_dek = row.wrapped_dek
        stored_hash = row.kek_id_hash
        expected_hash = self.kek_id_hash(self._kek)

        if stored_hash != expected_hash:
            raise KeyProviderError(
                f"KEK ID mismatch: expected {expected_hash}, found {stored_hash}. "
                "The KEK may have been rotated — set key_encryption_key_previous "
                "to the old KEK and restart."
            )

        return self.decrypt_with(wrapped_dek, self._kek)
