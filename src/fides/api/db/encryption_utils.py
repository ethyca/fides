from typing import Union

from sqlalchemy import Text
from sqlalchemy.types import TypeEngine
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.config import CONFIG

_cached_dek: str | None = None


def get_encryption_key() -> str:
    """
    Return the encryption key set in CONFIG.security.app_encryption_key.
    Cached for the lifetime of the process (called on every encrypt/decrypt).

    TODO: implement support for other key managers like AWS KMS
    """
    global _cached_dek
    if _cached_dek is not None:
        return _cached_dek
    _cached_dek = CONFIG.security.app_encryption_key
    return _cached_dek


def _reset_encryption_key_cache() -> None:
    """Reset the cached encryption key. For testing only."""
    global _cached_dek
    _cached_dek = None


def encrypted_type(
    type_in: Union[type[TypeEngine], TypeEngine, None] = None,
) -> StringEncryptedType:
    """Build a StringEncryptedType with a callable key."""
    if type_in is None:
        type_in = Text()
    return StringEncryptedType(
        type_in=type_in,
        key=get_encryption_key,  # callable, NOT called
        engine=AesGcmEngine,
        padding="pkcs5",
    )
