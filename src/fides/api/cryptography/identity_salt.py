import secrets
from functools import cache

from loguru import logger

from fides.api.api.deps import get_autoclose_db_session
from fides.api.models.identity_salt import IdentitySalt


@cache
def get_identity_salt() -> str:
    """
    Checks the database for the identity salt value and creates one if it doesn't exist.
    This function is cached to avoid repeated calls to the database for the same value.
    """

    with get_autoclose_db_session() as db:
        existing_salt = db.query(IdentitySalt).first()
        if existing_salt is None:
            new_salt = IdentitySalt.create(
                db, data={"encrypted_value": {"value": secrets.token_hex(32)}}
            )
            logger.info("Created new identity salt.")
            return new_salt.encrypted_value.get("value")

        logger.info("Caching existing identity salt.")
        return existing_salt.encrypted_value.get("value")
