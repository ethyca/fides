from typing import Optional, Dict, Any

from fides.api.schemas.redis_cache import Identity

from fides.api.util.cache import FidesopsRedis, get_cache
from loguru import logger


class DecryptedIdentityCacheMixin:
    """
    A class housing common decrypting identity cache logic for use as a mixin with
    any sqlalchemy model with an ID.
    """

    def _get_decrypted_identity_cache_key(self) -> str:
        """
        Returns the cache key at which the decrypted identities for a given privacy request are stored.
        """
        return f"DECRYPTED_IDENTITY__{self.id}"  # type: ignore

    def cache_decrypted_identities_by_privacy_request(self) -> None:
        """
        Cache the decrypted identity values for later fuzzy search comparison.
        Format: DECRYPTED_IDENTITY__{privacy_request_id} = {Identity Data}
        """
        cache: FidesopsRedis = get_cache()
        cache.set_with_autoexpire(
            key=self._get_decrypted_identity_cache_key(),
            value=FidesopsRedis.encode_obj(self.get_persisted_identity()),  # type: ignore
            expire_time=10800,  # 3 hrs
        )
