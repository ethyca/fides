from typing import Optional

from loguru import logger

from fides.api.common_exceptions import IdentityVerificationException
from fides.api.util.cache import FidesopsRedis, get_cache
from fides.config import CONFIG


class DecryptedIdentityCacheMixin:
    """
    A class housing common decrypting identity cache logic for use as a mixin with
    any sqlalchemy model with an ID.
    """

    def _get_has_cache_expired(self) -> bool:
        """Returns whether the decrypted identity cache has expired"""
        cache: FidesopsRedis = get_cache()
        cache.get_encoded_objects_by_prefix(
            "DECRYPTED_IDENTITY__CACHE_SIGNAL"
        )

    def _get_decrypted_identity_cache_key(self) -> str:
        """
        Returns the cache key at which the decrypted identities for a given privacy request are stored.
        """
        return f"DECRYPTED_IDENTITY__{self.privacy_request_id}"  # type: ignore

    def cache_decrypted_identities_by_privacy_request(self) -> None:
        """
        Cache the decrypted identity values for later fuzzy search comparison.
        Format: DECRYPTED_IDENTITY__{{privacy_request_id}} = {{all_decrypted_identity_types_for_req_id}}
        """
        cache: FidesopsRedis = get_cache()


        cache.set_with_autoexpire(
            key=self._get_decrypted_identity_cache_key(),
            value=self.encrypted_value,
            expire_time=10800,  # 3 hrs
        )
        # set deterministic 2nd key as a signal we can check to determine whether the cache has expired or not
        cache.set_with_autoexpire(
            key="DECRYPTED_IDENTITY__CACHE_SIGNAL",
            value=True,
            expire_time=10800,  # 3 hrs
        )
