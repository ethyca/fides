from joserfc import jwe
from joserfc.jwk import OctKey

_JWT_ENCRYPTION_ALGORITHM = "A256GCM"


def generate_jwe(payload: str, encryption_key: str, encoding: str = "UTF-8") -> str:
    """Generates a JWE with the provided payload.

    Returns a string representation.
    """
    key_bytes = (
        encryption_key.encode("utf-8")
        if isinstance(encryption_key, str)
        else encryption_key
    )
    key = OctKey.import_key(key_bytes)
    return jwe.encrypt_compact(
        {"alg": "dir", "enc": _JWT_ENCRYPTION_ALGORITHM},
        payload.encode(encoding),
        key,
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
    key_bytes = (
        encryption_key.encode("utf-8")
        if isinstance(encryption_key, str)
        else encryption_key
    )
    key = OctKey.import_key(key_bytes)
    result = jwe.decrypt_compact(token, key)
    return result.plaintext.decode(encoding)
