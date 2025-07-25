import secrets
from typing import Any, Dict, List, Optional, TypeVar

from loguru import logger

from fides.api.db.session import get_db_session
from fides.api.models.masking_secret import MaskingSecret
from fides.api.schemas.masking.masking_secrets import (
    MaskingSecretCache,
    MaskingSecretMeta,
    SecretType,
)
from fides.api.util.cache import get_cache, get_masking_secret_cache_key
from fides.config import CONFIG

T = TypeVar("T")


class SecretsUtil:
    @staticmethod
    def get_or_generate_secret(
        privacy_request_id: Optional[str],
        secret_type: SecretType,
        masking_secret_meta: MaskingSecretMeta[T],
    ) -> Optional[T]:
        if privacy_request_id is not None:
            secret = SecretsUtil.get_masking_secret(
                privacy_request_id=privacy_request_id,
                masking_strategy=masking_secret_meta.masking_strategy,
                secret_type=secret_type,
            )
            if not secret:
                logger.warning(
                    "Secret type {} expected but was not present for masking strategy {}",
                    secret_type,
                    masking_secret_meta.masking_strategy,
                )
            return secret

        # expected for standalone masking service
        return masking_secret_meta.generate_secret_func(
            masking_secret_meta.secret_length
        )

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

    @staticmethod
    def get_masking_secret(
        privacy_request_id: str,
        masking_strategy: str,
        secret_type: SecretType,
    ) -> Optional[Any]:
        """
        Attempts to retrieve masking secret from cache first, then falls back to DB.
        """
        # TODO: get rid of the cache check after a few releases
        # Try cache first
        cache = get_cache()
        cache_key = get_masking_secret_cache_key(
            privacy_request_id=privacy_request_id,
            masking_strategy=masking_strategy,
            secret_type=secret_type,
        )
        secret = cache.get_encoded_by_key(cache_key)
        if secret is not None:
            return secret

        # Cache miss - try database
        session_local = get_db_session(CONFIG)
        with session_local() as session:
            masking_secret: MaskingSecret = (
                session.query(MaskingSecret)
                .filter(
                    MaskingSecret.privacy_request_id == privacy_request_id,
                    MaskingSecret.masking_strategy == masking_strategy,
                    MaskingSecret.secret_type == secret_type,
                )
                .first()
            )

            if not masking_secret:
                return None

            return masking_secret.get_secret()
