from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MaskingConfiguration(BaseModel):
    """Base class for masking configuration"""


class FormatPreservationConfig(BaseModel):
    """option to preserve format in masking"""

    suffix: str


class StringRewriteMaskingConfiguration(MaskingConfiguration):
    """Configuration for the StringRewriteMaskingStrategy"""

    rewrite_value: str
    format_preservation: Optional[FormatPreservationConfig] = None


class HashMaskingConfiguration(MaskingConfiguration):
    """Configuration for the HashMaskingStrategy"""

    class Algorithm(Enum):
        """Denotes hashing algorithms supported by HashMaskingStrategy"""

        SHA_256 = "SHA-256"
        SHA_512 = "SHA-512"

    algorithm: Algorithm = Algorithm.SHA_256
    format_preservation: Optional[FormatPreservationConfig] = None


class AesEncryptionMaskingConfiguration(MaskingConfiguration):
    """Configuration for the AES encryption masking strategy"""

    class Mode(Enum):
        GCM = "GCM"

    mode: Mode = Mode.GCM
    format_preservation: Optional[FormatPreservationConfig] = None


class RandomStringMaskingConfiguration(MaskingConfiguration):
    """Configuration for the RandomStringRewriteMaskingStrategy"""

    length: int = 30
    format_preservation: Optional[FormatPreservationConfig] = None


class HmacMaskingConfiguration(MaskingConfiguration):
    """Configuration for the HmacMaskingStrategy"""

    class Algorithm(Enum):
        """Denotes hashing algorithms supported by HmacMaskingStrategy
        If none supplied, SHA-256 used by default.
        """

        sha_256 = "SHA-256"
        sha_512 = "SHA-512"

    algorithm: Algorithm = Algorithm.sha_256
    format_preservation: Optional[FormatPreservationConfig] = None


class NullMaskingConfiguration(MaskingConfiguration):
    """Configuration for the NullMaskingStrategy - this is the simplest masking strategy, no details are supplied"""
