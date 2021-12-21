import base64
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from fidesops.core.config import config
from fidesops.util.cryptographic_util import bytes_to_b64_str


def encrypt_to_bytes_verify_secrets_length(
    plain_value: Optional[str], key: bytes, nonce: bytes
) -> bytes:
    """Encrypts the value using the AES GCM Algorithm. Note that provided nonce must be 12 bytes.
    Returns encrypted value in bytes"""
    verify_nonce(nonce)
    verify_encryption_key(key)
    return _encrypt_to_bytes(plain_value, key, nonce)


def _encrypt_to_bytes(plain_value: Optional[str], key: bytes, nonce: bytes) -> bytes:
    """Encrypts the value using the AES GCM Algorithm. Note that provided nonce must be 12 bytes.
    Returns encrypted value in bytes"""
    if plain_value is None:
        raise ValueError("plain_value cannot be null")
    gcm = AESGCM(key)
    value_bytes = plain_value.encode(config.security.ENCODING)
    encrypted_bytes = gcm.encrypt(nonce, value_bytes, nonce)
    return encrypted_bytes


def encrypt_verify_secret_length(
    plain_value: Optional[str], key: bytes, nonce: bytes
) -> str:
    """Encrypts the value using the AES GCM Algorithm, with secret length verification.
    Returns encrypted value as a string"""
    encrypted: bytes = encrypt_to_bytes_verify_secrets_length(plain_value, key, nonce)
    return bytes_to_b64_str(encrypted)


def encrypt(plain_value: Optional[str], key: bytes, nonce: bytes) -> str:
    """Encrypts the value using the AES GCM Algorithm, without secret length verification.
    Returns encrypted value as a string"""
    encrypted: bytes = _encrypt_to_bytes(plain_value, key, nonce)
    return bytes_to_b64_str(encrypted)


def decrypt_combined_nonce_and_message(encrypted_value: str, key: bytes) -> str:
    """Decrypts a message when the nonce has been packaged together with the message"""
    verify_encryption_key(key)
    gcm = AESGCM(key)

    encrypted_combined: bytes = base64.b64decode(encrypted_value)
    # Separate the nonce out as the first 12 characters of the combined message
    nonce: bytes = encrypted_combined[0 : config.security.AES_GCM_NONCE_LENGTH]
    encrypted_message: bytes = encrypted_combined[
        config.security.AES_GCM_NONCE_LENGTH :
    ]

    decrypted_bytes: bytes = gcm.decrypt(nonce, encrypted_message, nonce)
    decrypted_str = decrypted_bytes.decode(config.security.ENCODING)
    return decrypted_str


def decrypt(encrypted_value: str, key: bytes, nonce: bytes) -> str:
    """Decrypts the value using the AES GCM Algorithm"""
    verify_encryption_key(key)
    verify_nonce(nonce)

    gcm = AESGCM(key)
    encrypted_bytes = base64.b64decode(encrypted_value)
    decrypted_bytes = gcm.decrypt(nonce, encrypted_bytes, nonce)
    decrypted_str = decrypted_bytes.decode(config.security.ENCODING)
    return decrypted_str


def verify_nonce(nonce: bytes) -> None:
    if len(nonce) != config.security.AES_GCM_NONCE_LENGTH:
        raise ValueError(
            f"Nonce must be {config.security.AES_GCM_NONCE_LENGTH} bytes long"
        )


def verify_encryption_key(key: bytes) -> None:
    if len(key) != config.security.AES_ENCRYPTION_KEY_LENGTH:
        raise ValueError(
            f"Encryption key must be {config.security.AES_ENCRYPTION_KEY_LENGTH} bytes long"
        )
