import secrets
from typing import Optional, Union

from fides.api.cryptography.cryptographic_util import bytes_to_b64_str
from fides.api.util.cache import get_dsr_cache_store
from fides.api.util.encryption.aes_gcm_encryption_scheme import (
    encrypt_to_bytes_verify_secrets_length,
)
from fides.config import CONFIG


def encrypt_access_request_results(data: Union[str, bytes], request_id: str) -> str:
    """Encrypt data with encryption key if provided, otherwise return unencrypted data.

    Args:
        data: The data to encrypt
        request_id: The ID of the privacy request for encryption key lookup

    Returns:
        str: The encrypted data as a string
    """
    if isinstance(data, bytes):
        data = data.decode(CONFIG.security.encoding)

    store = get_dsr_cache_store(request_id)
    raw = store.get_encryption("key")
    if raw is None:
        return data
    if isinstance(raw, bytes):
        encryption_key = raw.decode(CONFIG.security.encoding)
    else:
        encryption_key = str(raw)
    if not encryption_key:
        return data

    bytes_encryption_key: bytes = encryption_key.encode(
        encoding=CONFIG.security.encoding
    )
    nonce: bytes = secrets.token_bytes(CONFIG.security.aes_gcm_nonce_length)
    # b64encode the entire nonce and the encrypted message together
    return bytes_to_b64_str(
        nonce
        + encrypt_to_bytes_verify_secrets_length(data, bytes_encryption_key, nonce)
    )
