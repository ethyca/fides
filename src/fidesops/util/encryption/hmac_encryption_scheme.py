import hashlib
import hmac
from typing import Callable, Optional

from fidesops.core.config import config
from fidesops.schemas.masking.masking_configuration import HmacMaskingConfiguration


def hmac_encrypt_return_bytes(
    value: str,
    hmac_key: str,
    salt: str,
    hashing_algorithm: HmacMaskingConfiguration.Algorithm,
) -> bytes:
    return _hmac_encrypt(value, hmac_key, salt, hashing_algorithm).digest()


def hmac_encrypt_return_str(
    value: str,
    hmac_key: str,
    salt: str,
    hashing_algorithm: HmacMaskingConfiguration.Algorithm,
) -> str:
    return _hmac_encrypt(value, hmac_key, salt, hashing_algorithm).hexdigest()


def _hmac_encrypt(
    value: str,
    hmac_key: str,
    salt: str,
    hashing_algorithm: HmacMaskingConfiguration.Algorithm,
) -> hmac.HMAC:
    """Generic HMAC algorithm"""

    algorithm_function_mapping = {
        HmacMaskingConfiguration.Algorithm.sha_256: _hmac_sha256,
        HmacMaskingConfiguration.Algorithm.sha_512: _hmac_sha512,
    }

    algorithm_function: Optional[
        Callable[[str, str, str], hmac.HMAC]
    ] = algorithm_function_mapping.get(hashing_algorithm)
    return algorithm_function(value, hmac_key, salt)


def _hmac_sha256(value: str, hmac_key: str, salt: str) -> hmac.HMAC:
    """Creates a new hmac object using the sh256 hash algorithm and the hmac_key and then returns the hexdigest."""
    return _hmac(value=value, hmac_key=hmac_key, salt=salt, hashing_alg=hashlib.sha256)


def _hmac_sha512(value: str, hmac_key: str, salt: str) -> hmac.HMAC:
    """Creates a new hmac object using the sha512 hash algorithm and the hmac_key and then returns the hexdigest."""
    return _hmac(value=value, hmac_key=hmac_key, salt=salt, hashing_alg=hashlib.sha512)


def _hmac(value: str, hmac_key: str, salt: str, hashing_alg: Callable) -> hmac.HMAC:
    return hmac.new(
        key=hmac_key.encode(config.security.ENCODING),
        msg=(value + salt).encode(config.security.ENCODING),
        digestmod=hashing_alg,
    )
