import json
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, unquote_to_bytes

from bson.objectid import ObjectId
from loguru import logger
from redis import Redis
from redis.client import Script  # type: ignore
from redis.exceptions import ConnectionError as ConnectionErrorFromRedis

from fides.api import common_exceptions
from fides.api.schemas.masking.masking_secrets import SecretType
from fides.config import CONFIG

# This constant represents every type a redis key may contain, and can be
# extended if needed
RedisValue = Union[bytes, float, int, str]

_connection = None

ENCODED_BYTES_PREFIX = "quote_encoded_"
ENCODED_DATE_PREFIX = "date_encoded_"
ENCODED_MONGO_OBJECT_ID_PREFIX = "encoded_object_id_"


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:  # pylint: disable=too-many-return-statements
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, bytes):
            return f"{ENCODED_BYTES_PREFIX}{quote(o)}"
        if isinstance(o, (datetime, date)):
            return f"{ENCODED_DATE_PREFIX}{o.isoformat()}"
        if isinstance(o, ObjectId):
            return f"{ENCODED_MONGO_OBJECT_ID_PREFIX}{str(o)}"
        if isinstance(o, object):
            if hasattr(o, "__dict__"):
                return o.__dict__
            if not isinstance(o, int) and not isinstance(o, float):
                return str(o)

        # It doesn't seem possible to make it here, but I'm leaving in as a fail safe
        # just in case.
        return super().default(o)  # pragma: no cover


def _custom_decoder(json_dict: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in json_dict.items():
        if isinstance(v, str):
            # The mongodb objectids couldn't be directly json encoded so they are converted
            # to strings and prefixed with encoded_object_id in order to find during decodeint.
            if v.startswith(ENCODED_MONGO_OBJECT_ID_PREFIX):
                json_dict[k] = ObjectId(v[18:])
            if v.startswith(ENCODED_DATE_PREFIX):
                json_dict[k] = datetime.fromisoformat(v[13:])
            # The bytes from secrets couldn't be directly json encoded so it is url
            # encode and prefixed with quite_encoded in order to find during decodeint.
            elif v.startswith(ENCODED_BYTES_PREFIX):
                json_dict[k] = unquote_to_bytes(v)[14:]

    return json_dict


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
        dictionary. Note that if a key does not exist in redis it will be returned as None
        """
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
        """Encode an object to a JSON string that can be stored in Redis"""
        return json.dumps(obj, cls=CustomJSONEncoder)  # type: ignore

    @staticmethod
    def decode_obj(bs: Optional[str]) -> Optional[Dict[str, Any]]:
        """Decode an object from its JSON.

        Since Redis may not contain a value
        for a given key it's possible we may try to decode an empty object."""
        if bs:
            try:
                result = json.loads(bs, object_hook=_custom_decoder)
            except json.decoder.JSONDecodeError:
                # The cache used to be stored as a pickle. This decoder is unable
                # to decode the pickle object (this is on purpose) so None is returned
                # if a cache value is present in the old format rather the crashing.

                logger.info(
                    "Error decoding cache. If you are coming from a version of fides prior to 2.8 this could be an issue with cache format and the request needs to be reprocessed."
                )
                return None
            # Secrets are just a string and not dict so decode here.
            if isinstance(result, str) and result.startswith("quote_encoded"):
                result = unquote_to_bytes(result)[14:]
            return result
        return None


def get_cache(should_log: Optional[bool] = False) -> FidesopsRedis:
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
            username=CONFIG.redis.user,
            password=CONFIG.redis.password,
            ssl=CONFIG.redis.ssl,
            ssl_ca_certs=CONFIG.redis.ssl_ca_certs,
            ssl_cert_reqs=CONFIG.redis.ssl_cert_reqs,
        )
        if should_log:
            logger.debug("New Redis connection created.")

    if should_log:
        logger.debug("Testing Redis connection...")
    try:
        connected = _connection.ping()
    except ConnectionErrorFromRedis:
        connected = False
    else:
        if should_log:
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


def get_custom_privacy_request_field_cache_key(
    privacy_request_id: str, custom_privacy_request_field: str
) -> str:
    """Return the key at which to save this PrivacyRequest's custom field"""
    return f"id-{privacy_request_id}-custom-privacy-request-field-{custom_privacy_request_field}"


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
