from typing import Dict, Any, List, Optional

import ahocorasick
from fastapi import Query

from fides.api.models.privacy_request import PrivacyRequest

from fides.api.util.cache import FidesopsRedis, get_cache

from loguru import logger


DECRYPTED_IDENTITY_CACHE_KEY = "DECRYPTED_IDENTITY__CACHE_SIGNAL"


def set_decrypted_identity_cache_signal() -> None:
    """Set deterministic key as a signal we can check to determine whether the cache has expired or not"""
    cache: FidesopsRedis = get_cache()
    logger.info("Setting decrypted identity cache signal")
    cache.set_with_autoexpire(
        key=DECRYPTED_IDENTITY_CACHE_KEY,
        value="true",
        expire_time=10800,  # 3 hrs
    )


def remove_decrypted_identity_cache_signal() -> None:
    """Remove decrypted identity cache signal for testing"""
    cache: FidesopsRedis = get_cache()
    cache.delete_keys_by_prefix(DECRYPTED_IDENTITY_CACHE_KEY)


def get_has_identity_cache_expired() -> bool:
    """Returns whether the decrypted identity cache has expired"""
    cache: FidesopsRedis = get_cache()
    result = cache.get(
        DECRYPTED_IDENTITY_CACHE_KEY
    )
    if result:
        return False
    return True


def _add_decrypted_identities_to_automaton(identities: Dict[str, Any], request_id: str, automaton) -> None:
    for key, value in identities:
        if value:
            if automaton.exists(value):
                existing: List[str] = automaton.get(value)
                existing.append(str(request_id))
                # overwrites the previously found key, updates with new request id
                automaton.add_word(value, existing)
            else:
                automaton.add_word(value, [request_id])


def build_decrypted_identities_automaton(query: Query) -> ahocorasick.Automaton:
    """
    Retrieve identities from cache. If cache is expired, retrieves from DB and caches results.
    # Stores in automaton with format: {"decrypted identity val", ["req_id_1", "req_id_2"]}
    """
    automaton = ahocorasick.Automaton()

    all_privacy_requests: List[PrivacyRequest] = query.all()
    if get_has_identity_cache_expired():
        logger.info("Decrypted identity cache does not exist or has expired. Proceeding to cache all decrypted identities...")
        for request in all_privacy_requests:
            _add_decrypted_identities_to_automaton(request.get_persisted_identity().__dict__.items(), request.id, automaton)  # type: ignore
            # Write to cache for later
            request.cache_decrypted_identities_by_privacy_request()
        set_decrypted_identity_cache_signal()

    else:
        # Get identities from cache
        for request in all_privacy_requests:
            all_identities_for_request: Optional[Dict[str, Any]] = request.retrieve_decrypted_identities_from_cache_by_privacy_request()
            if not all_identities_for_request:
                # Safeguard if specific privacy requests do not have identities stored in the cache
                logger.info("Decrypted identities could not be found in cache for privacy request. Proceeding to look up in DB instead of using cache.")
                _add_decrypted_identities_to_automaton(request.get_persisted_identity.__dict__.items(), request.id, automaton)  # type: ignore
                # Write to cache for later
                request.cache_decrypted_identities_by_privacy_request()
            _add_decrypted_identities_to_automaton(all_identities_for_request.items(), request.id, automaton)  # type: ignore
    return automaton