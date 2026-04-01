"""Local envelope encryption provider using in-process AES-256-GCM."""

import base64
import binascii
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from sqlalchemy.orm import Session

from fides.api.models.encryption_key import EncryptionKey

from .base_provider import KeyProvider, KeyProviderError

# Fixed HMAC key for KEK identification. This is a protocol constant — changing
# it would invalidate all existing kek_id_hash values in the database.
_KEK_ID_HMAC_KEY = b"fides-kek-id"


class LocalKeyProvider(KeyProvider):
    """Envelope encryption provider using in-process AES-256-GCM.

    The KEK is supplied at construction time (from config). The wrapped DEK
    is stored in the encryption_keys database table.

    Note: get_dek() requires the encryption_keys table to be populated by the
    startup bootstrap task (PR 6). Until that lands, this provider should not
    be enabled in production.
    """

    def __init__(self, kek: str, session: Session) -> None:
        if len(kek.encode("UTF-8")) != 32:
            raise KeyProviderError("KEK must be exactly 32 bytes")
        self._kek = kek.encode("UTF-8")
        self._session = session

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(kek=***, session={self._session!r})"

    @staticmethod
    def kek_id_hash(kek: str) -> str:
        """Compute a truncated HMAC that identifies a KEK without leaking it.

        Uses a fixed domain-separation key so the hash is deterministic
        for a given KEK but reveals nothing about the key material.
        """
        digest = hmac.new(
            key=_KEK_ID_HMAC_KEY,
            msg=kek.encode("UTF-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        return digest[:16]

    @staticmethod
    def _pack(nonce: bytes, tag: bytes, ciphertext: bytes) -> str:
        """Encode nonce + tag + ciphertext as a base64 string.

        Base64 encoding is needed because the raw bytes may contain null bytes
        or non-UTF-8 sequences that can't be stored safely in a TEXT column.
        """
        return base64.b64encode(nonce + tag + ciphertext).decode("UTF-8")

    @staticmethod
    def _unpack(encoded: str) -> tuple[bytes, bytes, bytes]:
        """Decode a base64 string into (nonce, tag, ciphertext)."""
        try:
            raw = base64.b64decode(encoded)
        except binascii.Error as exc:
            raise KeyProviderError("Invalid base64 in wrapped DEK") from exc

        if len(raw) <= 28:
            raise KeyProviderError(
                "Wrapped DEK too short — expected at least 29 bytes (12 nonce + 16 tag + ciphertext)"
            )

        return raw[:12], raw[12:28], raw[28:]

    def encrypt_dek(self, dek: str) -> str:
        """Encrypt a DEK with the configured KEK using AES-256-GCM.

        Returns base64(nonce[12] + tag[16] + ciphertext).
        """
        # 96-bit random nonce, as recommended for AES-GCM
        nonce = os.urandom(12)

        # Use the KEK directly as the AES-256 key (32 bytes from 32 UTF-8 chars).
        # This differs from aes_gcm_encryption_util.py which SHA-256 hashes the
        # key for SQLAlchemy-Utils compatibility — here we skip that step because
        # the KEK is already the correct length.
        cipher = Cipher(
            algorithms.AES(self._kek),
            modes.GCM(nonce),
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(dek.encode("UTF-8")) + encryptor.finalize()

        return self._pack(nonce, encryptor.tag, ciphertext)

    @staticmethod
    def decrypt_with(encrypted_dek: str, kek: str) -> str:
        """Decrypt an encrypted DEK using the given KEK.

        This is public so that KEK rotation can decrypt with the previous
        KEK before re-encrypting with the new one.
        """
        nonce, tag, ciphertext = LocalKeyProvider._unpack(encrypted_dek)
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
                "Failed to decrypt DEK — the KEK may be incorrect or the "
                "encrypted DEK may be corrupt"
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
        expected_hash = self.kek_id_hash(self._kek.decode("UTF-8"))

        if stored_hash != expected_hash:
            raise KeyProviderError(
                f"KEK ID mismatch: expected {expected_hash}, found {stored_hash}. "
                "The KEK may have been rotated — set key_encryption_key_previous "
                "to the old KEK and restart."
            )

        return self.decrypt_with(wrapped_dek, self._kek.decode("UTF-8"))
