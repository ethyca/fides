import secrets

from fastapi import Security
from loguru import logger

from fides.api.cryptography import cryptographic_util
from fides.api.cryptography.cryptographic_util import b64_str_to_bytes, bytes_to_b64_str
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.encryption_request import (
    AesDecryptionRequest,
    AesDecryptionResponse,
    AesEncryptionRequest,
    AesEncryptionResponse,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.encryption.aes_gcm_encryption_scheme import (
    decrypt as aes_gcm_decrypt,
)
from fides.api.util.encryption.aes_gcm_encryption_scheme import (
    encrypt_verify_secret_length as aes_gcm_encrypt,
)
from fides.common.api.scope_registry import ENCRYPTION_EXEC
from fides.common.api.v1.urn_registry import (
    DECRYPT_AES,
    ENCRYPT_AES,
    ENCRYPTION_KEY,
    V1_URL_PREFIX,
)
from fides.config import CONFIG

router = APIRouter(tags=["Encryption"], prefix=V1_URL_PREFIX)


@router.get(
    ENCRYPTION_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[ENCRYPTION_EXEC])],
    response_model=str,
)
def get_encryption_key() -> str:
    logger.info("Generating encryption key")
    return cryptographic_util.generate_secure_random_string(
        CONFIG.security.aes_encryption_key_length
    )


@router.put(
    ENCRYPT_AES,
    dependencies=[Security(verify_oauth_client, scopes=[ENCRYPTION_EXEC])],
    response_model=AesEncryptionResponse,
)
def aes_encrypt(encryption_request: AesEncryptionRequest) -> AesEncryptionResponse:
    logger.info("Starting AES Encryption")
    nonce: bytes = secrets.token_bytes(CONFIG.security.aes_gcm_nonce_length)

    encrypted_value: str = aes_gcm_encrypt(
        encryption_request.value,
        encryption_request.key,  # type: ignore
        nonce,
    )
    return AesEncryptionResponse(
        encrypted_value=encrypted_value, nonce=bytes_to_b64_str(nonce)
    )


@router.put(
    DECRYPT_AES,
    dependencies=[Security(verify_oauth_client, scopes=[ENCRYPTION_EXEC])],
    response_model=AesDecryptionResponse,
)
def aes_decrypt(decryption_request: AesDecryptionRequest) -> AesDecryptionResponse:
    logger.info("Starting AES Decryption")
    nonce: bytes = b64_str_to_bytes(decryption_request.nonce)

    decrypted_value: str = aes_gcm_decrypt(
        decryption_request.value,
        decryption_request.key.encode(CONFIG.security.encoding),
        nonce,
    )
    return AesDecryptionResponse(decrypted_value=decrypted_value)
