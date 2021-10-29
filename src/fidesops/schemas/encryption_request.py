from pydantic import BaseModel


class AesEncryptionRequest(BaseModel):
    """Specifies fields provided to the AES Encryption endpoint"""

    value: str
    key: str


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
