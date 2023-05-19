import secrets
from typing import Dict, List, Optional, TypeVar

from loguru import logger

from fides.api.schemas.masking.masking_secrets import (
    MaskingSecretCache,
    MaskingSecretMeta,
    SecretType,
)
from fides.api.util.cache import get_cache, get_masking_secret_cache_key

T = TypeVar("T")


class SecretsUtil:
    @staticmethod
    def get_or_generate_secret(
        privacy_request_id: Optional[str],
        secret_type: SecretType,
        masking_secret_meta: MaskingSecretMeta[T],
    ) -> Optional[T]:
        if privacy_request_id is not None:
            secret = SecretsUtil._get_secret_from_cache(
                privacy_request_id, secret_type, masking_secret_meta
            )
            if not secret:
                logger.warning(
                    "Secret type {} expected from cache but was not present for masking strategy {}",
                    secret_type,
                    masking_secret_meta.masking_strategy,
                )
            return secret

        # expected for standalone masking service
        return masking_secret_meta.generate_secret_func(
            masking_secret_meta.secret_length
        )

    @staticmethod
    def _get_secret_from_cache(
        privacy_request_id: str,
        secret_type: SecretType,
        masking_secret_meta: MaskingSecretMeta[T],
    ) -> Optional[T]:
        cache = get_cache()
        masking_secret_cache_key: str = get_masking_secret_cache_key(
            privacy_request_id=privacy_request_id,
            masking_strategy=masking_secret_meta.masking_strategy,
            secret_type=secret_type,
        )
        return cache.get_encoded_by_key(masking_secret_cache_key)

    @staticmethod
    def generate_secret_string(length: int) -> str:
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_secret_bytes(length: int) -> bytes:
        return secrets.token_bytes(length)

    @staticmethod
    def build_masking_secrets_for_cache(
        masking_secret_meta: Dict[SecretType, MaskingSecretMeta[T]],
    ) -> List[MaskingSecretCache[T]]:
        masking_secrets = []
        for secret_type in masking_secret_meta.keys():
            meta = masking_secret_meta[secret_type]
            secret: T = meta.generate_secret_func(meta.secret_length)
            masking_secrets.append(
                MaskingSecretCache[T](  # type: ignore
                    secret=secret,
                    masking_strategy=meta.masking_strategy,
                    secret_type=secret_type,
                )
            )
        return masking_secrets
