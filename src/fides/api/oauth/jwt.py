from jose import jwe
from jose.constants import ALGORITHMS

_JWT_ENCRYPTION_ALGORITHM = ALGORITHMS.A256GCM


def generate_jwe(payload: str, encryption_key: str, encoding: str = "UTF-8") -> str:
    """Generates a JWE with the provided payload.

    Returns a string representation.
    """
    return jwe.encrypt(
        payload,
        encryption_key,
        encryption=_JWT_ENCRYPTION_ALGORITHM,
    ).decode(encoding)


def decrypt_jwe(token: str, encryption_key: str, encoding: str = "UTF-8") -> str:
    """Decrypts a JWE token and returns the payload as a string.

    Args:
        token: The JWE token to decrypt.
        encryption_key: The key used to decrypt the token.
        encoding: The encoding to use for the decrypted payload.

    Returns:
        The decrypted payload as a string.
    """
    decrypted_payload = jwe.decrypt(
        token,
        encryption_key,
    )
    return decrypted_payload.decode(encoding)
