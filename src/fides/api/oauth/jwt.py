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
