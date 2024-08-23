from typing import Optional, Dict, Any

from fides.api.util.cache import FidesopsRedis, get_cache


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

    def retrieve_decrypted_identities_from_cache_by_privacy_request(self) -> Optional[Dict[str, Any]]:
        """
        Returns the decrypted identity values for a given privacy request.
        Format: {"email": "test@email.com", "phone_number": None}
        """
        cache: FidesopsRedis = get_cache()
        return FidesopsRedis.decode_obj(cache.get(self._get_decrypted_identity_cache_key()))

    def remove_decrypted_identities_from_cache_by_privacy_request(self) -> None:
        """
        Remove the decrypted identity values from the cache. Used for testing.
        """
        cache: FidesopsRedis = get_cache()
        cache.delete_keys_by_prefix(self._get_decrypted_identity_cache_key())
