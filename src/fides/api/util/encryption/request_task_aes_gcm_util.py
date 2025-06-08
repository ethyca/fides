# pylint: disable=protected-access
"""
AES GCM encryption utilities specifically for RequestTask external storage data.

This module provides encryption/decryption functions that use the same key and engine
as the database columns to ensure consistency across the application.
"""

import json
from typing import List

from loguru import logger
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.util.collection_util import Row
from fides.api.util.custom_json_encoder import CustomJSONEncoder, _custom_decoder
from fides.config import CONFIG


class RequestTaskEncryptionError(Exception):
    """Raised when encryption/decryption operations fail"""


def encrypt_data(data: List[Row]) -> bytes:
    """
    Serialize and encrypt data using CustomJSONEncoder and AesGcmEngine

    Args:
        data: Raw data to serialize and encrypt

    Returns:
        Encrypted bytes

    Raises:
        RequestTaskEncryptionError: If serialization or encryption fails
    """
    try:
        # First serialize using CustomJSONEncoder for consistent ObjectId handling
        serialized_data = json.dumps(data, cls=CustomJSONEncoder, separators=(",", ":"))
        data_bytes = serialized_data.encode("utf-8")

        # Then encrypt
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
            f"Serialized and encrypted {len(data_bytes)} bytes to {len(encrypted_bytes)} bytes"
        )
        return encrypted_bytes
    except Exception as e:
        logger.error(f"Failed to serialize/encrypt data: {e}")
        raise RequestTaskEncryptionError(f"Failed to serialize/encrypt data: {str(e)}")


def decrypt_data(encrypted_bytes: bytes) -> List[Row]:
    """
    Decrypt and deserialize data using AesGcmEngine and _custom_decoder

    Args:
        encrypted_bytes: Encrypted data bytes to decrypt

    Returns:
        Deserialized data

    Raises:
        RequestTaskEncryptionError: If decryption or deserialization fails
    """
    try:
        # First decrypt
        engine = AesGcmEngine()
        # Use the same key as database columns
        key = CONFIG.security.app_encryption_key
        engine._update_key(key)
        # Convert bytes to string for decryption, as AesGcmEngine expects string input
        encrypted_str = encrypted_bytes.decode("utf-8")
        decrypted_data = engine.decrypt(encrypted_str)

        # Then deserialize using _custom_decoder for consistent ObjectId handling
        data = json.loads(decrypted_data, object_hook=_custom_decoder)
        logger.debug(
            f"Decrypted and deserialized {len(encrypted_bytes)} bytes to {len(data)} records"
        )
        return data
    except Exception as e:
        logger.error(f"Failed to decrypt/deserialize data: {e}")
        raise RequestTaskEncryptionError(
            f"Failed to decrypt/deserialize data: {str(e)}"
        )
