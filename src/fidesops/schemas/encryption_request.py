from pydantic import BaseModel, validator

from fidesops.core.config import config
from fidesops.util.encryption.aes_gcm_encryption_scheme import verify_encryption_key


class AesEncryptionRequest(BaseModel):
    """Specifies fields provided to the AES Encryption endpoint"""

    value: str
    key: str

    @validator("key")
    def validate_key(cls, v: str) -> bytes:
        """Convert string into bytes and verify this is the correct length"""
        key = v.encode(config.security.ENCODING)
        verify_encryption_key(key)
        return key


class AesEncryptionResponse(BaseModel):
    """Specifies fields returned from the AES Encryption endpoint"""

    encrypted_value: str
    nonce: str


class AesDecryptionRequest(BaseModel):
    """Specifies fields provided to the AES Decryption endpoint"""

    value: str
    key: str
    nonce: str


class AesDecryptionResponse(BaseModel):
    """Specified fields returned from the AES Decryption endpoint"""

    decrypted_value: str
