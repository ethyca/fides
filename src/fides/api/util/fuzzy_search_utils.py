from typing import Any, Dict, List, Optional

import ahocorasick  # type: ignore
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.util.cache import FidesopsRedis, get_cache
from fides.config import get_config

AUTOMATON_SIGNAL_CACHE_KEY = "DECRYPTED_IDENTITY_AUTOMATON__CACHE_SIGNAL"
CONFIG = get_config()
_automaton = None


def get_decrypted_identities_automaton(
    db: Session, check_for_cache: bool = False
) -> ahocorasick.Automaton:  # pylint: disable=c-extension-no-member
    """
    Return a singleton Automaton that we can use for efficient fuzzy search.

    If check_for_cache is true, we refresh the automaton if automaton age is > 3 hrs.
    Automatons are only refreshed during new privacy requests (not during search) to reduce chance of slow performance
    during search.

    More background:

    Because we use SQLAlchemy-level AES/GCM encryption to write identity data to our ProvidedIdentity table,
    we cannot implement fuzzy search at the DB-level. No tools exist that support an equivalent AES/GCM decryption
    method within Postgres.

    Instead, we implement fuzzy search by decrypting identity data at the app-level. We do this by storing
    decrypted identity data in a singleton that refreshes every 3 hrs.

    We also manually write to the singleton when new privacy requests are created so that we do not miss newer values.
    """
    global _automaton  # pylint: disable=W0603
    if _automaton is None:
        logger.info(
            "Automaton does not yet exist. Proceeding to build automaton with decrypted identities..."
        )
        _automaton = build_automaton(db)
    elif check_for_cache and get_should_refresh_automaton():
        logger.info(
            "Automaton has expired. Proceeding to build new automaton with decrypted identities..."
        )
        _automaton = build_automaton(db)

    # Else use global pre-existing singleton
    return _automaton


def manually_reset_automaton() -> None:
    """Manually set our global _automaton singleton to None. Used for testing"""
    global _automaton  # pylint: disable=W0603
    _automaton = None


def build_automaton(
    db: Session,
) -> ahocorasick.Automaton:  # pylint: disable=c-extension-no-member
    """
    Builds automaton in this format: {"decrypted identity val", ["req_id_1", "req_id_2"]}
    """
    # Local import to avoid circular dependencies
    from fides.api.models.privacy_request import PrivacyRequest

    logger.debug("Creating new automaton...")
    automaton = ahocorasick.Automaton()  # pylint: disable=c-extension-no-member
    all_privacy_requests: List[PrivacyRequest] = db.query(PrivacyRequest).yield_per(1000)  # type: ignore
    for request in all_privacy_requests:
        _add_decrypted_identities_to_automaton(request.get_persisted_identity().__dict__, request.id, automaton)  # type: ignore
    set_automaton_cache_signal()
    return automaton


def add_identity_to_automaton(
    automaton: ahocorasick.Automaton,  # pylint: disable=c-extension-no-member
    request_id: str,
    identities: Optional[Dict[str, Any]],
) -> None:
    logger.info("Adding single identity to automaton...")
    _add_decrypted_identities_to_automaton(identities, request_id, automaton)


def set_automaton_cache_signal() -> None:
    """Set a signal we can check to determine whether we should refresh our decrypted identity automaton"""
    cache: FidesopsRedis = get_cache()
    logger.info("Setting automaton cache signal")
    cache.set_with_autoexpire(
        key=AUTOMATON_SIGNAL_CACHE_KEY,
        value="true",
        expire_time=10800,  # 3 hrs
    )


def remove_refresh_automaton_signal() -> None:
    """Remove should refresh automaton signal from cache for testing"""
    cache: FidesopsRedis = get_cache()
    cache.delete_keys_by_prefix(AUTOMATON_SIGNAL_CACHE_KEY)


def get_should_refresh_automaton() -> bool:
    """Returns whether we should refresh our decrypted identity automaton"""
    cache: FidesopsRedis = get_cache()
    result = cache.get(AUTOMATON_SIGNAL_CACHE_KEY)
    if result:
        return False
    return True


def _add_decrypted_identities_to_automaton(
    identities: Optional[Dict[str, Any]],
    request_id: str,
    automaton: ahocorasick.Automaton,  # pylint: disable=c-extension-no-member
) -> None:
    if not identities or not identities.items():
        return
    for key, value in identities.items():  # pylint: disable=W0612
        if value:
            if automaton.exists(value):
                existing: List[str] = automaton.get(value)  # value = decrypted identity
                existing.append(str(request_id))
                # overwrites the previously found key, updates with new request id
                automaton.add_word(value, existing)
            else:
                automaton.add_word(value, [request_id])
