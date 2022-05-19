from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class SecretType(Enum):
    """Enum that holds all possible types of secrets across all masking strategies"""

    key = "key"
    salt = "salt"
    # the below types are used by the AES algorithm, when it calls HMAC to generate the nonce
    key_hmac = "key_hmac"
    salt_hmac = "salt_hmac"


@dataclass(unsafe_hash=True)
class MaskingSecretMeta(Generic[T]):
    """Holds metadata describing one secret"""

    masking_strategy: str
    generate_secret_func: Callable[[int], T]
    # currently length is the same for all masking secrets, but just in case we want to specify in future
    secret_length: int = 32


@dataclass
class MaskingSecretCache(Generic[T]):
    """Information required to cache a secret"""

    secret: T
    masking_strategy: str
    secret_type: SecretType
