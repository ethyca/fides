"""
AES GCM encryption utilities specifically for RequestTask external storage data.

This module provides encryption/decryption functions that use the same key and engine
as the database columns to ensure consistency across the application.
"""

from loguru import logger
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.config import CONFIG


class RequestTaskEncryptionError(Exception):
    """Raised when encryption/decryption operations fail"""


def encrypt_data(data_bytes: bytes) -> bytes:
    """
    Encrypt data bytes using AesGcmEngine with the same key as database columns

    Args:
        data_bytes: Raw data bytes to encrypt

    Returns:
        Encrypted bytes

    Raises:
        RequestTaskEncryptionError: If encryption fails
    """
    try:
        engine = AesGcmEngine()
        # Use the same key as database columns
        key = CONFIG.security.app_encryption_key
        engine._update_key(key)
        # Convert bytes to string for encryption, as AesGcmEngine expects string input
        data_str = data_bytes.decode("utf-8")
        encrypted_data = engine.encrypt(data_str)
        # Convert encrypted string back to bytes for storage
        encrypted_bytes = encrypted_data.encode("utf-8")
        logger.debug(
            f"Encrypted {len(data_bytes)} bytes to {len(encrypted_bytes)} bytes"
        )
        return encrypted_bytes
    except Exception as e:
        logger.error(f"Failed to encrypt data: {e}")
        raise RequestTaskEncryptionError(f"Failed to encrypt data: {str(e)}")


def decrypt_data(encrypted_bytes: bytes) -> bytes:
    """
    Decrypt data bytes using AesGcmEngine with the same key as database columns

    Args:
        encrypted_bytes: Encrypted data bytes to decrypt

    Returns:
        Decrypted bytes

    Raises:
        RequestTaskEncryptionError: If decryption fails
    """
    try:
        engine = AesGcmEngine()
        # Use the same key as database columns
        key = CONFIG.security.app_encryption_key
        engine._update_key(key)
        # Convert bytes to string for decryption, as AesGcmEngine expects string input
        encrypted_str = encrypted_bytes.decode("utf-8")
        decrypted_data = engine.decrypt(encrypted_str)
        # Convert decrypted string back to bytes
        decrypted_bytes = decrypted_data.encode("utf-8")
        logger.debug(
            f"Decrypted {len(encrypted_bytes)} bytes to {len(decrypted_bytes)} bytes"
        )
        return decrypted_bytes
    except Exception as e:
        logger.error(f"Failed to decrypt data: {e}")
        raise RequestTaskEncryptionError(f"Failed to decrypt data: {str(e)}")
