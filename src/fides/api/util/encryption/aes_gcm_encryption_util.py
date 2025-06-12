"""
AES GCM encryption utilities with SQLAlchemy-Utils and cryptography library implementations.

This module provides simplified encrypt/decrypt functions using two approaches:
1. SQLAlchemy-Utils AesGcmEngine (compatible with existing database encryption)
2. Cryptography library with chunked processing (better performance, standard library)
"""

import base64
import hashlib
import json
import os
from typing import Any, List, Optional, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from loguru import logger
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.util.collection_util import Row
from fides.api.util.custom_json_encoder import CustomJSONEncoder, _custom_decoder
from fides.config import CONFIG


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail"""


# SQLAlchemy-Utils Implementation (for compatibility with existing database encryption)
def encrypt_with_sqlalchemy_utils(data: List[Row]) -> bytes:
    """
    Serialize and encrypt data using CustomJSONEncoder and SQLAlchemy-Utils AesGcmEngine.

    This approach is compatible with existing database encryption but has lower performance.

    Args:
        data: Raw data to serialize and encrypt

    Returns:
        Encrypted bytes

    Raises:
        EncryptionError: If serialization or encryption fails
    """
    try:
        # Serialize using CustomJSONEncoder for consistent ObjectId handling
        serialized_data = json.dumps(data, cls=CustomJSONEncoder, separators=(",", ":"))
        data_bytes = serialized_data.encode("utf-8")

        # Encrypt using SQLAlchemy-Utils AesGcmEngine
        engine = AesGcmEngine()
        key = CONFIG.security.app_encryption_key
        engine._update_key(key)  # pylint: disable=protected-access

        # AesGcmEngine expects string input
        data_str = data_bytes.decode("utf-8")
        encrypted_data = engine.encrypt(data_str)
        encrypted_bytes = encrypted_data.encode("utf-8")

        logger.debug(
            f"SQLAlchemy-Utils: Encrypted {len(data_bytes)} bytes to {len(encrypted_bytes)} bytes"
        )
        return encrypted_bytes

    except Exception as e:
        logger.error(f"SQLAlchemy-Utils encryption failed: {e}")
        raise EncryptionError(f"SQLAlchemy-Utils encryption failed: {str(e)}")


def decrypt_with_sqlalchemy_utils(encrypted_bytes: bytes) -> List[Row]:
    """
    Decrypt and deserialize data using SQLAlchemy-Utils AesGcmEngine and _custom_decoder.

    Args:
        encrypted_bytes: Encrypted data bytes to decrypt

    Returns:
        Deserialized data

    Raises:
        EncryptionError: If decryption or deserialization fails
    """
    try:
        # Decrypt using SQLAlchemy-Utils AesGcmEngine
        engine = AesGcmEngine()
        key = CONFIG.security.app_encryption_key
        engine._update_key(key)  # pylint: disable=protected-access

        # AesGcmEngine expects string input
        encrypted_str = encrypted_bytes.decode("utf-8")
        decrypted_data = engine.decrypt(encrypted_str)

        # Deserialize using _custom_decoder for consistent ObjectId handling
        data = json.loads(decrypted_data, object_hook=_custom_decoder)

        logger.debug(
            f"SQLAlchemy-Utils: Decrypted {len(encrypted_bytes)} bytes to {len(data)} records"
        )
        return data

    except Exception as e:
        logger.error(f"SQLAlchemy-Utils decryption failed: {e}")
        raise EncryptionError(f"SQLAlchemy-Utils decryption failed: {str(e)}")


# Cryptography Library Implementation (standard, chunked processing)
def encrypt_with_cryptography(
    data: Union[List[Row], Any], chunk_size: Optional[int] = None
) -> bytes:
    """
    Serialize and encrypt data using the standard cryptography library with chunked processing.

    This provides fast performance and memory efficiency for large datasets.

    Args:
        data: Raw data to serialize and encrypt
        chunk_size: Size of chunks for processing (default 4MB)

    Returns:
        Encrypted bytes (base64-encoded string as bytes)

    Raises:
        EncryptionError: If serialization or encryption fails
    """
    try:
        # Set default chunk size
        if chunk_size is None:
            chunk_size = 4 * 1024 * 1024  # 4MB chunks

        # Serialize using CustomJSONEncoder for consistent handling
        serialized_data = json.dumps(data, cls=CustomJSONEncoder, separators=(",", ":"))
        plaintext = serialized_data.encode("utf-8")

        data_size_mb = len(plaintext) / (1024 * 1024)
        chunk_size_mb = chunk_size / (1024 * 1024)
        estimated_chunks = len(plaintext) // chunk_size + (
            1 if len(plaintext) % chunk_size else 0
        )
        record_count = len(data) if isinstance(data, list) else "N/A"

        logger.info(
            f"Cryptography: Encrypting {record_count} records ({data_size_mb:.1f} MB) "
            f"using {chunk_size_mb:.0f}MB chunks (~{estimated_chunks} chunks)"
        )

        # Use SQLAlchemy-Utils compatible key (SHA256 hash of app key)
        key = _get_sqlalchemy_compatible_key()
        nonce = os.urandom(12)  # 96-bit nonce for AES-GCM

        # Create cipher
        cipher = Cipher(
            algorithms.AES(key), modes.GCM(nonce), backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Process in chunks for memory efficiency
        ciphertext_chunks = []
        for i in range(0, len(plaintext), chunk_size):
            chunk = plaintext[i : i + chunk_size]
            ciphertext_chunks.append(encryptor.update(chunk))

        # Finalize and get tag
        encryptor.finalize()
        tag = encryptor.tag

        # Combine in same format as SQLAlchemy-Utils: [nonce/iv][tag][ciphertext]
        ciphertext = b"".join(ciphertext_chunks)
        binary_result = nonce + tag + ciphertext

        # Base64 encode to match SQLAlchemy-Utils format
        base64_result = base64.b64encode(binary_result).decode("utf-8")
        result_bytes = base64_result.encode("utf-8")

        encrypted_size_mb = len(result_bytes) / (1024 * 1024)
        logger.info(
            f"Cryptography: Encrypted successfully - "
            f"{len(ciphertext_chunks)} chunks, {encrypted_size_mb:.1f} MB output (base64)"
        )

        return result_bytes

    except Exception as e:
        logger.error(f"Cryptography encryption failed: {e}")
        raise EncryptionError(f"Cryptography encryption failed: {str(e)}")


def decrypt_with_cryptography(
    encrypted_bytes: bytes, chunk_size: Optional[int] = None
) -> Union[List[Row], Any]:
    """
    Decrypt and deserialize data using the cryptography library with chunked processing.

    Args:
        encrypted_bytes: Encrypted data (base64-encoded string as bytes)
        chunk_size: Size of chunks for processing (default 4MB)

    Returns:
        Deserialized data

    Raises:
        EncryptionError: If decryption or deserialization fails
    """
    try:
        # Set default chunk size
        if chunk_size is None:
            chunk_size = 4 * 1024 * 1024  # 4MB chunks

        # Decode from base64
        encrypted_str = encrypted_bytes.decode("utf-8")
        binary_data = base64.b64decode(encrypted_str)

        # Extract components in SQLAlchemy-Utils format: [nonce/iv][tag][ciphertext]
        if len(binary_data) < 28:  # 12 (nonce) + 16 (tag)
            raise ValueError("Encrypted data too short")

        nonce = binary_data[:12]  # First 12 bytes: nonce/IV
        tag = binary_data[12:28]  # Next 16 bytes: tag
        ciphertext = binary_data[28:]  # Remaining bytes: ciphertext

        encrypted_size_mb = len(encrypted_bytes) / (1024 * 1024)
        chunk_size_mb = chunk_size / (1024 * 1024)
        estimated_chunks = len(ciphertext) // chunk_size + (
            1 if len(ciphertext) % chunk_size else 0
        )

        logger.info(
            f"Cryptography: Decrypting {encrypted_size_mb:.1f} MB "
            f"using {chunk_size_mb:.0f}MB chunks (~{estimated_chunks} chunks)"
        )

        # Use SQLAlchemy-Utils compatible key
        key = _get_sqlalchemy_compatible_key()
        cipher = Cipher(
            algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # Process in chunks for memory efficiency
        plaintext_chunks = []
        for i in range(0, len(ciphertext), chunk_size):
            chunk = ciphertext[i : i + chunk_size]
            plaintext_chunks.append(decryptor.update(chunk))

        # Finalize
        decryptor.finalize()

        # Combine and deserialize
        plaintext = b"".join(plaintext_chunks)
        decrypted_json = plaintext.decode("utf-8")
        data = json.loads(decrypted_json, object_hook=_custom_decoder)

        record_count = len(data) if isinstance(data, list) else "N/A"
        logger.info(f"Cryptography: Successfully decrypted {record_count} records")

        return data

    except Exception as e:
        logger.error(f"Cryptography decryption failed: {e}")
        raise EncryptionError(f"Cryptography decryption failed: {str(e)}")


def _get_sqlalchemy_compatible_key() -> bytes:
    """Get 32-byte encryption key compatible with SQLAlchemy-Utils AesGcmEngine."""
    app_key = CONFIG.security.app_encryption_key.encode(CONFIG.security.encoding)
    # SQLAlchemy-Utils always uses SHA256 hash of the key
    return hashlib.sha256(app_key).digest()


# Public API - Use cryptography by default for new operations
encrypt_data = encrypt_with_cryptography
decrypt_data = decrypt_with_cryptography
