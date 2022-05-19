import logging
import secrets

from fastapi import APIRouter, Security

from fidesops.api.v1.scope_registry import ENCRYPTION_EXEC
from fidesops.api.v1.urn_registry import (
    DECRYPT_AES,
    ENCRYPT_AES,
    ENCRYPTION_KEY,
    V1_URL_PREFIX,
)
from fidesops.core.config import config
from fidesops.schemas.encryption_request import (
    AesDecryptionRequest,
    AesDecryptionResponse,
    AesEncryptionRequest,
    AesEncryptionResponse,
)
from fidesops.util import cryptographic_util
from fidesops.util.cryptographic_util import b64_str_to_bytes, bytes_to_b64_str
from fidesops.util.encryption.aes_gcm_encryption_scheme import (
    decrypt as aes_gcm_decrypt,
)
from fidesops.util.encryption.aes_gcm_encryption_scheme import (
    encrypt_verify_secret_length as aes_gcm_encrypt,
)
from fidesops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Encryption"], prefix=V1_URL_PREFIX)


logger = logging.getLogger(__name__)


@router.get(
    ENCRYPTION_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[ENCRYPTION_EXEC])],
    response_model=str,
)
def get_encryption_key() -> str:
    logger.info("Generating encryption key")
    return cryptographic_util.generate_secure_random_string(
        config.security.AES_ENCRYPTION_KEY_LENGTH
    )


@router.put(
    ENCRYPT_AES,
    dependencies=[Security(verify_oauth_client, scopes=[ENCRYPTION_EXEC])],
    response_model=AesEncryptionResponse,
)
def aes_encrypt(encryption_request: AesEncryptionRequest) -> AesEncryptionResponse:
    logger.info("Starting AES Encryption")
    nonce: bytes = secrets.token_bytes(config.security.AES_GCM_NONCE_LENGTH)

    encrypted_value: str = aes_gcm_encrypt(
        encryption_request.value,
        encryption_request.key,
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
        decryption_request.key.encode(config.security.ENCODING),
        nonce,
    )
    return AesDecryptionResponse(decrypted_value=decrypted_value)
