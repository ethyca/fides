import logging
from typing import Optional

from fides.api.ops.common_exceptions import IdentityVerificationException
from fides.api.ops.util.cache import (
    FidesopsRedis,
    get_cache,
)

from fides.ctl.core.config import get_config


logger = logging.getLogger(__name__)
CONFIG = get_config()


class IdentityVerificationMixin:
    """
    A class housing common identity verification logic for use as a mixin with
    any sqlalchemy model with an ID.
    """

    def _get_identity_verification_cache_key(self) -> str:
        """ """
        return f"IDENTITY_VERIFICATION_CODE__{self.id}"

    def _get_identity_verification_attempt_count_cache_key(self) -> str:
        """ """
        return self._get_identity_verification_cache_key() + "__attempt_count"

    def cache_identity_verification_code(self, value: str) -> None:
        """Cache the generated identity verification code for later comparison."""
        cache: FidesopsRedis = get_cache()
        cache.set_with_autoexpire(
            key=self._get_identity_verification_cache_key(),
            value=value,
        )
        cache.set_with_autoexpire(
            key=self._get_identity_verification_attempt_count_cache_key(),
            value=0,
        )

    def _increment_verification_code_attempt_count(self) -> None:
        """Cache the generated identity verification code for later comparison."""
        cache: FidesopsRedis = get_cache()
        attempt_count: int = self._get_cached_verification_code_attempt_count()
        cache.set_with_autoexpire(
            key=self._get_identity_verification_attempt_count_cache_key(),
            value=attempt_count + 1,
        )

    def get_cached_verification_code(self) -> Optional[str]:
        """Retrieve the generated identity verification code if it exists"""
        cache = get_cache()
        values = cache.get_values([self._get_identity_verification_cache_key()]) or {}
        if not values:
            return None

        return values.get(self._get_identity_verification_cache_key(), None)

    def _get_cached_verification_code_attempt_count(self) -> int:
        """Retrieve the generated identity verification code if it exists"""
        cache = get_cache()
        attempts = cache.get(self._get_identity_verification_attempt_count_cache_key())
        if not attempts:
            attempts = "0"
        return int(attempts)

    def purge_verification_code(self) -> None:
        """Removes any verification codes from the cache so they can no longer be used."""
        cache = get_cache()
        cache.delete(self._get_identity_verification_cache_key())
        cache.delete(self._get_identity_verification_attempt_count_cache_key())

    def verify_identity(self, provided_code: str) -> object:
        """Verify the identification code supplied by the user."""
        code: Optional[str] = self.get_cached_verification_code()
        if not code:
            raise IdentityVerificationException(
                f"Identification code expired for {self.id}."
            )

        attempt_count: int = self._get_cached_verification_code_attempt_count()
        if attempt_count >= CONFIG.security.identity_verification_attempt_limit:
            # When the attempt_count we can remove the verification code entirely
            # from the cache to ensure it can never be used again.
            self.purge_verification_code()
            raise PermissionError(f"Attempt limit hit for '{self.id}'")

        self._increment_verification_code_attempt_count()
        if code != provided_code:
            raise PermissionError(f"Incorrect identification code for '{self.id}'")

        # This code should only be successfully used once, so purge here now that's happened.
        self.purge_verification_code()
        return self
