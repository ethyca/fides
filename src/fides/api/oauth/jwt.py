from functools import lru_cache

from joserfc import jwe
from joserfc.jwk import OctKey

JWT_ENCRYPTION_ALGORITHM = "A256GCM"


# Cache size is set to 3 somewhat arbitrarily. We currently don't allow
# encryption key rotation so we should effectively only have a single
# value in this cache. When we implement key rotation, there should only
# ever be 2 keys in use at a time, so 3 should be enough.
# This will need to be re-thought if we ever support multiple different
# encryption keys for encrypting tokens.
@lru_cache(maxsize=3)
def _get_oct_key(key_bytes: bytes) -> OctKey:
    """Cache the OctKey so it's built once per distinct key value."""
    return OctKey.import_key(key_bytes)


def _to_oct_key(encryption_key: str) -> OctKey:
    key_bytes = (
        encryption_key.encode("utf-8")
        if isinstance(encryption_key, str)
        else encryption_key
    )
    return _get_oct_key(key_bytes)


def generate_jwe(payload: str, encryption_key: str, encoding: str = "UTF-8") -> str:
    """Generates a JWE with the provided payload.

    Returns a string representation.
    """
    return jwe.encrypt_compact(
        {"alg": "dir", "enc": JWT_ENCRYPTION_ALGORITHM},
        payload.encode(encoding),
        _to_oct_key(encryption_key),
    )


def decrypt_jwe(token: str, encryption_key: str, encoding: str = "UTF-8") -> str:
    """Decrypts a JWE token and returns the payload as a string.

    Args:
        token: The JWE token to decrypt.
        encryption_key: The key used to decrypt the token.
        encoding: The encoding to use for the decrypted payload.

    Returns:
        The decrypted payload as a string.
    """
    result = jwe.decrypt_compact(token, _to_oct_key(encryption_key))
    if result.plaintext is None:
        raise ValueError("JWE decryption produced no plaintext")
    return result.plaintext.decode(encoding)
