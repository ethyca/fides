import base64
import pickle
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from redis import Redis
from redis.client import Script  # type: ignore
from redis.exceptions import ConnectionError as ConnectionErrorFromRedis

from fides.api.ops import common_exceptions
from fides.api.ops.schemas.masking.masking_secrets import SecretType
from fides.core.config import get_config

CONFIG = get_config()

# This constant represents every type a redis key may contain, and can be
# extended if needed
RedisValue = Union[bytes, float, int, str]

_connection = None


class FidesopsRedis(Redis):
    """
    An extension to Redis' python bindings to support auto expiring data input. This class
    should never be instantiated on its own.
    """

    def set_with_autoexpire(
        self,
        key: str,
        value: RedisValue,
        expire_time: int = CONFIG.redis.default_ttl_seconds,
    ) -> Optional[bool]:
        """Call the connection class' default set method with ex= our default TTL"""
        if not expire_time:
            # We have to check this condition for the edge case where `None` is explicitly
            # passed to this method.
            expire_time = CONFIG.redis.default_ttl_seconds
        return self.set(key, value, ex=expire_time)

    def get_keys_by_prefix(self, prefix: str, chunk_size: int = 1000) -> List[str]:
        """Retrieve all keys that match a given prefix."""
        cursor: Any = "0"
        out = []
        while cursor != 0:
            cursor, keys = self.scan(
                cursor=cursor, match=f"{prefix}*", count=chunk_size
            )
            out.extend(keys)
        return out

    def delete_keys_by_prefix(self, prefix: str) -> None:
        """Delete all keys starting with a given prefix"""
        s: Script = self.register_script(
            f"for _,k in ipairs(redis.call('keys','{prefix}*')) do redis.call('del',k) end"
        )
        s()

    def get_values(self, keys: List[str]) -> Dict[str, Optional[Any]]:
        """Retrieve all values corresponding to the set of input keys and return them as a
        dictionary. Note that if a key does not exist in redis it will be returned as None"""
        values = self.mget(keys)
        return {x[0]: x[1] for x in zip(keys, values)}

    def set_encoded_object(self, key: str, obj: Any) -> Optional[bool]:
        """Set an object in redis in an encoded form. This object should be retrieved via
        get_objects_by_prefix or processed with decode_obj."""
        return self.set_with_autoexpire(f"EN_{key}", FidesopsRedis.encode_obj(obj))

    def get_encoded_by_key(self, key: str) -> Optional[Any]:
        """Returns cached obj decoded from base64"""
        val = super().get(key)
        return self.decode_obj(val) if val else None

    def get_encoded_objects_by_prefix(self, prefix: str) -> Dict[str, Optional[Any]]:
        """Return all objects stored under a given prefix. This method
        assumes these objects have been stored encoded using set_object"""
        keys = self.get_keys_by_prefix(f"EN_{prefix}")
        encoded_object_dict = self.get_values(keys)
        return {
            key: FidesopsRedis.decode_obj(value)
            for key, value in encoded_object_dict.items()
        }

    @staticmethod
    def encode_obj(obj: Any) -> bytes:
        """Encode an object to a base64 string that can be stored in Redis"""
        return base64.b64encode(pickle.dumps(obj))

    @staticmethod
    def decode_obj(bs: Optional[bytes]) -> Any:
        """Decode an object from its base64 representation.

        Since Redis may not contain a value
        for a given key it's possible we may try to decode an empty object."""
        if bs:
            return pickle.loads(base64.b64decode(bs))
        return None


def get_cache() -> FidesopsRedis:
    """Return a singleton connection to our Redis cache"""
    global _connection  # pylint: disable=W0603
    if _connection is None:
        logger.debug("Creating new Redis connection...")
        _connection = FidesopsRedis(  # type: ignore[call-overload]
            charset=CONFIG.redis.charset,
            decode_responses=CONFIG.redis.decode_responses,
            host=CONFIG.redis.host,
            port=CONFIG.redis.port,
            db=CONFIG.redis.db_index,
            password=CONFIG.redis.password,
            ssl=CONFIG.redis.ssl,
            ssl_cert_reqs=CONFIG.redis.ssl_cert_reqs,
        )
        logger.debug("New Redis connection created.")

    logger.debug("Testing Redis connection...")
    try:
        connected = _connection.ping()
    except ConnectionErrorFromRedis:
        connected = False
    else:
        logger.debug("Redis connection succeeded.")

    if not connected:
        logger.debug("Redis connection failed.")
        raise common_exceptions.RedisConnectionError(
            "Unable to establish Redis connection. Fidesops is unable to accept PrivacyRequsts."
        )

    return _connection


def get_identity_cache_key(privacy_request_id: str, identity_attribute: str) -> str:
    """Return the key at which to save this PrivacyRequest's identity for the passed in attribute"""
    # TODO: Remove this prefix
    return f"id-{privacy_request_id}-identity-{identity_attribute}"


def get_drp_request_body_cache_key(
    privacy_request_id: str, identity_attribute: str
) -> str:
    """Return the key at which to save this PrivacyRequest's drp request body for the passed in attribute"""
    return f"id-{privacy_request_id}-drp-{identity_attribute}"


def get_encryption_cache_key(privacy_request_id: str, encryption_attr: str) -> str:
    """Return the key at which to save this PrivacyRequest's encryption attribute"""
    return f"id-{privacy_request_id}-encryption-{encryption_attr}"


def get_masking_secret_cache_key(
    privacy_request_id: str, masking_strategy: str, secret_type: SecretType
) -> str:
    """Return the key at which to save this PrivacyRequest's masking secret attribute"""
    return (
        f"id-{privacy_request_id}-masking-secret-{masking_strategy}-{secret_type.value}"
    )


def get_all_cache_keys_for_privacy_request(privacy_request_id: str) -> List[Any]:
    """Returns all cache keys related to this privacy request's cached identities"""
    cache: FidesopsRedis = get_cache()
    return cache.keys(f"{privacy_request_id}-*") + cache.keys(
        f"id-{privacy_request_id}-*"
    )


def get_async_task_tracking_cache_key(privacy_request_id: str) -> str:
    return f"id-{privacy_request_id}-async-execution"
