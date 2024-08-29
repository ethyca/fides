import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote_to_bytes

from loguru import logger
from redis import Redis
from redis.client import Script  # type: ignore
from redis.exceptions import ConnectionError as ConnectionErrorFromRedis
from redis.exceptions import DataError

from fides.api import common_exceptions
from fides.api.schemas.masking.masking_secrets import SecretType
from fides.api.tasks import (
    MESSAGING_QUEUE_NAME,
    PRIVACY_PREFERENCES_QUEUE_NAME,
    celery_app,
)
from fides.api.util.custom_json_encoder import CustomJSONEncoder, _custom_decoder
from fides.config import CONFIG

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


def cache_task_tracking_key(request_id: str, celery_task_id: str) -> None:
    """
    Cache the celery task id created to run the Privacy Request or Request Task.

    Note that it is possible a Privacy Request or Request Task is queued multiple times
    over the life of a Privacy Request so the cached id is the latest task queued

    :param request_id: Can be the Privacy Request Id or a Request Task ID - these are cached in the same place.
    :param celery_task_id: The id of the Celery task itself that was queued to run the
    Privacy Request or the Request Task
    :return: None
    """

    cache: FidesopsRedis = get_cache()

    try:
        cache.set(
            get_async_task_tracking_cache_key(request_id),
            celery_task_id,
        )
    except DataError:
        logger.debug(
            "Error tracking task_id for privacy request or request task with id {}",
            request_id,
        )


def celery_tasks_in_flight(celery_task_ids: List[str]) -> bool:
    """Returns True if supplied Celery Tasks appear to be in-flight"""
    if not celery_task_ids:
        return False

    queried_tasks = celery_app.control.inspect().query_task(*celery_task_ids)
    if not queried_tasks:
        return False

    # Expected format: {HOSTNAME: {TASK_ID: [STATE, TASK_INFO]}}
    for _, task_details in queried_tasks.items():
        for _, state_array in task_details.items():
            state: str = state_array[0]
            # Note, not positive of states here,
            # some seen in testing, some from here:
            # https://github.com/celery/celery/blob/main/celery/worker/control.py or
            # https://github.com/celery/celery/blob/main/celery/states.py
            if state in [
                "active",
                "received",
                "registered",
                "reserved",
                "retry",
                "scheduled",
                "started",
            ]:
                return True

    return False


def get_queue_counts() -> Dict[str, int]:
    """
    Returns a count of the list of the tasks in each queue
    """
    try:
        queue_counts: Dict[str, int] = {}
        redis_conn = get_cache()
        default_queue_name = celery_app.conf.get("task_default_queue", "celery")
        for queue in [
            MESSAGING_QUEUE_NAME,
            PRIVACY_PREFERENCES_QUEUE_NAME,
            default_queue_name,
        ]:
            queue_counts[queue] = redis_conn.llen(queue)
    except Exception as exception:
        logger.critical(exception)
        queue_counts = {}
    return queue_counts
